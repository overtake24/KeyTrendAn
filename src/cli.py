import typer
import asyncio
import yaml
from rich.console import Console

from .database import Database
from .scraper import get_scraper
from .analyzer import Analyzer
from .output import OutputManager

app = typer.Typer()
console = Console()


@app.command()
def add_source(
        category: str = typer.Argument(..., help="Kategori"),
        name: str = typer.Argument(..., help="Kaynak adı"),
        url: str = typer.Argument(..., help="Kaynak URL'si"),
        source_type: str = typer.Option("api", help="Kaynak tipi (api, web)"),
        auth_type: str = typer.Option(None, help="Kimlik doğrulama tipi"),
        auth_credentials: str = typer.Option(None, help="Kimlik bilgileri"),
        scrape_method: str = typer.Option("simple", help="Kazıma yöntemi")
):
    """Yeni veri kaynağı ekle"""
    asyncio.run(_add_source(category, name, url, source_type, auth_type, auth_credentials, scrape_method))


async def _add_source(category, name, url, source_type, auth_type, auth_credentials, scrape_method):
    db = Database()
    await db.init()
    await db.add_source(category, name, url, source_type, auth_type, auth_credentials, scrape_method)
    console.print(f"[green]Kaynak eklendi:[/green] {name} ({category})")
    await db.close()


@app.command()
def research(
        category: str = typer.Argument(..., help="Araştırılacak kategori"),
        limit: int = typer.Option(10, help="Sonuç limiti"),
        output_file: str = typer.Option("research.json", help="Çıktı dosyası")
):
    """Belirtilen kategorideki kaynaklarla araştırma yap"""
    asyncio.run(_research(category, limit, output_file))


async def _research(category, limit, output_file):
    db = Database()
    await db.init()
    sources = await db.get_sources_by_category(category)

    if not sources:
        console.print(f"[yellow]Uyarı:[/yellow] '{category}' kategorisinde kaynak bulunamadı.")
        return

    # Konfigürasyon dosyasından anahtar kelimeleri al
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)

    keywords = config["niches"].get(category, {}).get("keywords", [])
    if not keywords:
        console.print(f"[yellow]Uyarı:[/yellow] '{category}' kategorisinde anahtar kelime bulunamadı.")
        return

    console.print(f"[blue]{len(sources)} kaynak üzerinde araştırma yapılıyor...[/blue]")

    all_results = []
    for source in sources:
        scraper = get_scraper(source)
        async with scraper:  # Context manager kullanımı
            results = await scraper.scrape(keywords, limit=limit)

        for result in results:
            await db.save_trends(
                category,
                result["keyword"],
                result["source"],
                result["data"]
            )
            all_results.append(result)

    console.print(f"[green]Araştırma tamamlandı![/green]")

    # Sonuçları dosyaya kaydet
    output = OutputManager(format="json")
    output.save_to_file(all_results, output_file)

    await db.close()


@app.command()
def analyze(
        category: str = typer.Argument(..., help="Analiz edilecek kategori"),
        keyword: str = typer.Option(None, help="Anahtar kelime filtresi"),
        days: int = typer.Option(7, help="Kaç günlük veri"),
        format: str = typer.Option("terminal", help="Çıktı formatı (terminal, json)"),
        output_file: str = typer.Option("analysis.json", help="Çıktı dosyası (JSON formatı için)")
):
    """Kazınmış verileri analiz et"""
    asyncio.run(_analyze(category, keyword, days, format, output_file))


async def _analyze(category, keyword, days, format, output_file):
    db = Database()
    await db.init()
    data = await db.get_trends(category, keyword, days)

    if not data:
        console.print(f"[yellow]Uyarı:[/yellow] Analiz edilecek veri bulunamadı.")
        return

    analyzer = Analyzer(data)
    results = analyzer.run_analysis()

    output = OutputManager(format=format)
    output.display(results)

    if format == "json" or output_file:
        output.save_to_file(results, output_file)

    await db.close()


@app.command()
def scrape(
        category: str = typer.Argument(..., help="Kazınacak kategori"),
        output_file: str = typer.Option("trends.json", help="Çıktı dosyası")
):
    """Belirtilen kategorideki trendleri kazı"""
    asyncio.run(_scrape(category, output_file))


async def _scrape(category, output_file):

    # Konfigürasyon dosyasından anahtar kelimeleri ve kaynakları al
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)

    if category not in config["niches"]:
        console.print(f"[red]Hata:[/red] '{category}' kategorisi bulunamadı.")
        return

    niche_config = config["niches"][category]
    keywords = niche_config["keywords"]
    source_names = niche_config["sources"]

    console.print(f"[blue]{len(source_names)} kaynak üzerinde {len(keywords)} anahtar kelime kazınıyor...[/blue]")

    # Basitlik için varsayılan kaynak yapılandırmaları
    sources = [{"name": name} for name in source_names]

    db = Database()
    await db.init()

    all_results = []
    for source in sources:
        scraper = get_scraper(source)
        async with scraper:  # Context manager kullanımı
            results = await scraper.scrape(keywords)

            for result in results:
                await db.save_trends(
                    category,
                    result["keyword"],
                    result["source"],
                    result["data"]
                )
                all_results.append(result)

    console.print(f"[green]Kazıma tamamlandı! {len(all_results)} sonuç bulundu.[/green]")

    # Sonuçları dosyaya kaydet
    output = OutputManager(format="json")
    output.save_to_file(all_results, output_file)

    await db.close()


if __name__ == "__main__":
    app()