import typer
import asyncio
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import box

from .database import Database
from .scraper import get_scraper
from .analyzer import Analyzer
from .output import OutputManager

app = typer.Typer(help="Anahtar kelime trend analiz aracı")
console = Console()


@app.command()
def add_source(
        category: str = typer.Argument(..., help="Kategori adı"),
        name: str = typer.Argument(..., help="Kaynak adı"),
        url: str = typer.Argument(..., help="Kaynak URL'si"),
        source_type: str = typer.Option("api", help="Kaynak tipi (api, web)"),
        auth_type: str = typer.Option(None, help="Kimlik doğrulama tipi"),
        auth_credentials: str = typer.Option(None, help="Kimlik bilgileri"),
        scrape_method: str = typer.Option("simple", help="Kazıma yöntemi")
):
    """Yeni bir veri kaynağı ekler"""
    console.print(Panel("Veri Kaynağı Ekleniyor", style="blue", box=box.ROUNDED))
    asyncio.run(_add_source(category, name, url, source_type, auth_type, auth_credentials, scrape_method))


async def _add_source(category, name, url, source_type, auth_type, auth_credentials, scrape_method):
    try:
        async with Database() as db:
            await db.add_source(category, name, url, source_type, auth_type, auth_credentials, scrape_method)
            console.print(Panel(f"[green]Kaynak eklendi:[/green] {name} ({category})", style="green", box=box.ROUNDED))
    except Exception as e:
        console.print(Panel(f"[bold red]Hata:[/bold red] {str(e)}", style="red", box=box.ROUNDED))
        import traceback
        console.print(traceback.format_exc())


@app.command()
def research(
        category: str = typer.Argument(..., help="Araştırılacak kategori"),
        limit: int = typer.Option(10, help="Sonuç limiti"),
        output_file: str = typer.Option("research.json", help="Çıktı dosyası")
):
    """Belirtilen kategorideki kaynaklarla araştırma yap"""
    console.print(Panel(f"[bold]{category}[/bold] Kategorisi İçin Araştırma", style="blue", box=box.ROUNDED))
    asyncio.run(_research(category, limit, output_file))


async def _research(category, limit, output_file):
    try:
        async with Database() as db:
            sources = await db.get_sources_by_category(category)

            if not sources:
                console.print(
                    Panel(f"[yellow]Uyarı:[/yellow] '{category}' kategorisinde kaynak bulunamadı.", style="yellow",
                          box=box.ROUNDED))
                return

            # Konfigürasyon dosyasından anahtar kelimeleri al
            with open("config/config.yaml", "r") as f:
                config = yaml.safe_load(f)

            keywords = config["niches"].get(category, {}).get("keywords", [])
            if not keywords:
                console.print(Panel(f"[yellow]Uyarı:[/yellow] '{category}' kategorisinde anahtar kelime bulunamadı.",
                                    style="yellow", box=box.ROUNDED))
                return

            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
            ) as progress:
                task = progress.add_task(f"[cyan]Araştırma yapılıyor...", total=len(sources) * len(keywords))

                all_results = []
                completed = 0

                for source in sources:
                    scraper = get_scraper(source)
                    async with scraper:
                        results = await scraper.scrape(keywords, limit=limit)

                        for result in results:
                            await db.save_trends(
                                category,
                                result["keyword"],
                                result["source"],
                                result["data"]
                            )
                            all_results.append(result)
                            completed += 1
                            progress.update(task, completed=completed)

            console.print(
                Panel(f"[green]Araştırma tamamlandı![/green] {len(all_results)} sonuç bulundu.", style="green",
                      box=box.ROUNDED))

            # Sonuçları dosyaya kaydet
            output = OutputManager(format="json")
            output.save_to_file(all_results, output_file)

    except Exception as e:
        console.print(Panel(f"[bold red]Hata:[/bold red] {str(e)}", style="red", box=box.ROUNDED))
        import traceback
        console.print(traceback.format_exc())


@app.command()
def analyze(
        category: str = typer.Argument(..., help="Analiz edilecek kategori"),
        keyword: str = typer.Option(None, help="Anahtar kelime filtresi"),
        days: int = typer.Option(7, help="Kaç günlük veri"),
        format: str = typer.Option("terminal", help="Çıktı formatı (terminal, json)"),
        output_file: str = typer.Option("analysis.json", help="Çıktı dosyası (JSON formatı için)")
):
    """Kazınmış verileri analiz et"""
    console.print(Panel(f"[bold]{category}[/bold] Kategorisi İçin Analiz", style="blue", box=box.ROUNDED))
    asyncio.run(_analyze(category, keyword, days, format, output_file))


async def _analyze(category, keyword, days, format, output_file):
    try:
        async with Database() as db:
            data = await db.get_trends(category, keyword, days)

            if not data:
                console.print(
                    Panel(f"[yellow]Uyarı:[/yellow] Analiz edilecek veri bulunamadı.", style="yellow", box=box.ROUNDED))
                return

            analyzer = Analyzer(data)
            results = analyzer.run_analysis()

            output = OutputManager(format=format)
            output.display(results)

            if format == "json" or output_file:
                output.save_to_file(results, output_file)

    except Exception as e:
        console.print(Panel(f"[bold red]Hata:[/bold red] {str(e)}", style="red", box=box.ROUNDED))
        import traceback
        console.print(traceback.format_exc())


@app.command()
def scrape(
        category: str = typer.Argument(..., help="Kazınacak kategori"),
        output_file: str = typer.Option("trends.json", help="Çıktı dosyası")
):
    """Belirtilen kategorideki trendleri kazır"""
    console.print(Panel(f"[bold]{category}[/bold] Kategorisi İçin Trend Kazıma", style="green", box=box.ROUNDED))
    asyncio.run(_scrape(category, output_file))


async def _scrape(category, output_file):
    try:
        # Konfigürasyon dosyasından anahtar kelimeleri ve kaynakları al
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)

        if category not in config["niches"]:
            console.print(
                Panel(f"[bold red]Hata:[/bold red] '{category}' kategorisi bulunamadı.", style="red", box=box.ROUNDED))
            return

        niche_config = config["niches"][category]
        keywords = niche_config["keywords"]
        source_names = niche_config["sources"]

        # Progress bar ekleyelim
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task(f"[cyan]Kazıma işlemi: {len(source_names)} kaynak, {len(keywords)} anahtar kelime",
                                     total=len(source_names) * len(keywords))

            # Basitlik için varsayılan kaynak yapılandırmaları
            sources = [{"name": name} for name in source_names]

            async with Database() as db:
                all_results = []
                completed = 0

                for source in sources:
                    scraper = get_scraper(source)
                    async with scraper:
                        results = await scraper.scrape(keywords)

                        for result in results:
                            await db.save_trends(
                                category,
                                result["keyword"],
                                result["source"],
                                result["data"]
                            )
                            all_results.append(result)
                            completed += 1
                            progress.update(task, completed=completed)

            console.print(
                Panel(f"[bold green]Kazıma tamamlandı! [/bold green]{len(all_results)} sonuç bulundu.", style="green",
                      box=box.ROUNDED))

            # Sonuçları dosyaya kaydet
            output = OutputManager(format="json")
            output.save_to_file(all_results, output_file)

    except Exception as e:
        console.print(Panel(f"[bold red]Hata:[/bold red] {str(e)}", style="red", box=box.ROUNDED))
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    app()