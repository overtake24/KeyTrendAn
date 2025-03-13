import typer
import asyncio
import yaml
import json
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from src.scraper.hybrid_manager import HybridScrapingManager, close_all_browsers

app = typer.Typer(help="Hibrit Anahtar Kelime Trend Analiz Aracı")
console = Console()


@app.command()
def login(
        service: str = typer.Argument(..., help="Giriş yapılacak servis (twitter, google)"),
        browser: str = typer.Option("chromium", help="Kullanılacak tarayıcı (chromium, firefox, webkit)")
):
    """Servislere giriş yap ve oturumu kaydet"""
    console.print(Panel(f"[bold]{service.capitalize()}[/bold] Servisine Giriş", style="blue", box=box.ROUNDED))
    asyncio.run(_login(service, browser))


async def _login(service, browser_type="chromium"):
    try:
        # Tarayıcıyı manuel başlat - browser tipini seç
        manager = HybridScrapingManager(keep_open=True, browser_type=browser_type)
        await manager.init_browser()

        if service.lower() == "twitter":
            success = await manager.twitter_login()
        elif service.lower() == "google":
            success = await manager.google_login()
        else:
            console.print(
                Panel(f"[bold red]Hata:[/bold red] Desteklenmeyen servis: {service}", style="red", box=box.ROUNDED))
            return

        if success:
            console.print(Panel(f"[green]Giriş başarılı ve oturum kaydedildi![/green] Tarayıcı penceresi açık kalacak.",
                                style="green", box=box.ROUNDED))
            # Context'i kapat ama tarayıcıyı açık tut
            await manager.close_context()
        else:
            console.print(
                Panel(f"[yellow]Uyarı:[/yellow] Giriş tamamlanamadı veya oturum kaydedilemedi.", style="yellow",
                      box=box.ROUNDED))

    except Exception as e:
        console.print(Panel(f"[bold red]Hata:[/bold red] {str(e)}", style="red", box=box.ROUNDED))
        import traceback
        console.print(traceback.format_exc())


@app.command()
def scrape(
        category: str = typer.Argument(..., help="Kazınacak kategori"),
        output_file: str = typer.Option("trends.json", help="Çıktı dosyası"),
        limit: int = typer.Option(10, help="Her kaynak için sonuç limiti"),
        browser: str = typer.Option("chromium", help="Kullanılacak tarayıcı (chromium, firefox, webkit)")
):
    """Belirtilen kategorideki trendleri hibrit mod ile kazı"""
    console.print(Panel(f"[bold]{category}[/bold] Kategorisi İçin Hibrit Trend Kazıma", style="green", box=box.ROUNDED))
    asyncio.run(_scrape(category, output_file, limit, browser))


async def _scrape(category, output_file, limit, browser_type="chromium"):
    try:
        # Konfigürasyon dosyasından anahtar kelimeleri ve kaynakları al
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            console.print(Panel(f"[bold red]Hata:[/bold red] config/config.yaml dosyası bulunamadı.", style="red",
                                box=box.ROUNDED))
            return

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if category not in config["niches"]:
            console.print(
                Panel(f"[bold red]Hata:[/bold red] '{category}' kategorisi bulunamadı.", style="red", box=box.ROUNDED))
            return

        niche_config = config["niches"][category]
        keywords = niche_config["keywords"]
        sources = niche_config.get("sources", [])

        # Desteklenen hibrit kaynakları filtrele
        hybrid_sources = [s for s in sources if s in ["google_trends", "twitter"]]

        if not hybrid_sources:
            console.print(
                Panel(f"[yellow]Uyarı:[/yellow] '{category}' kategorisinde desteklenen hibrit kaynak bulunamadı.",
                      style="yellow", box=box.ROUNDED))
            return

        if not keywords:
            console.print(
                Panel(f"[yellow]Uyarı:[/yellow] '{category}' kategorisinde anahtar kelime bulunamadı.", style="yellow",
                      box=box.ROUNDED))
            return

        # Oturum dizinini kontrol et
        session_dir = "browser_sessions"
        os.makedirs(session_dir, exist_ok=True)

        # Her kaynak için oturum dosyası var mı kontrol et
        sessions_needed = []
        if "google_trends" in hybrid_sources and not os.path.exists(f"{session_dir}/google_session"):
            sessions_needed.append("google")
        if "twitter" in hybrid_sources and not os.path.exists(f"{session_dir}/twitter_session"):
            sessions_needed.append("twitter")

        # Gerekli oturumlar için giriş yap
        for service in sessions_needed:
            console.print(f"[yellow]{service.capitalize()} oturumu bulunamadı. Giriş yapmanız gerekiyor.[/yellow]")
            await _login(service, browser_type)

        console.print(f"Hibrit scraper başlatılıyor... ({browser_type} tarayıcısı kullanılıyor)")

        # Progress bar
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task(
                f"[cyan]Kazıma işlemi: {len(hybrid_sources)} kaynak, {len(keywords)} anahtar kelime",
                total=len(hybrid_sources) * len(keywords))

            all_results = []
            completed = 0

            # HybridScrapingManager'ı oluşturup, tarayıcıyı aç
            manager = HybridScrapingManager(keep_open=True, browser_type=browser_type)

            # Google Trends verileri
            if "google_trends" in hybrid_sources:
                await manager.init_browser(session_name="google_session")
                for keyword in keywords:
                    trends_data, screenshot = await manager.get_google_trends_data(keyword)
                    result = {
                        "keyword": keyword,
                        "source": "google_trends",
                        "data": trends_data["trends"] if trends_data else {},
                        "related_queries": trends_data["related_queries"] if trends_data else [],
                        "screenshot": screenshot
                    }
                    all_results.append(result)
                    completed += 1
                    progress.update(task, completed=completed)
                await manager.close_context()  # Sadece context'i kapat

            # Twitter verileri
            if "twitter" in hybrid_sources:
                await manager.init_browser(session_name="twitter_session")
                for keyword in keywords:
                    tweets, screenshot = await manager.get_twitter_data(keyword, limit)
                    result = {
                        "keyword": keyword,
                        "source": "twitter",
                        "data": tweets,
                        "screenshot": screenshot
                    }
                    all_results.append(result)
                    completed += 1
                    progress.update(task, completed=completed)
                await manager.close_context()  # Sadece context'i kapat

        console.print(Panel(f"[green]Kazıma tamamlandı![/green] {len(all_results)} sonuç bulundu.", style="green",
                            box=box.ROUNDED))
        console.print(
            "[bold yellow]Tarayıcı penceresi açık bırakıldı. İşlemlerinizi gözlemleyebilirsiniz.[/bold yellow]")

        # Sonuçları dosyaya kaydet
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        console.print(f"[green]Sonuçlar {output_file} dosyasına kaydedildi![/green]")

        # Ekran görüntülerinin listesini göster
        screenshots = [result["screenshot"] for result in all_results if result.get("screenshot")]
        if screenshots:
            console.print("\n[bold]Alınan ekran görüntüleri:[/bold]")
            for ss in screenshots:
                console.print(f"  - {ss}")

    except Exception as e:
        console.print(Panel(f"[bold red]Hata:[/bold red] {str(e)}", style="red", box=box.ROUNDED))
        import traceback
        console.print(traceback.format_exc())


@app.command()
def close(
        browser: str = typer.Option("chromium", help="Kapatılacak tarayıcı (chromium, firefox, webkit)")
):
    """Tüm tarayıcı pencerelerini kapat"""
    console.print(
        Panel(f"[bold]{browser.capitalize()}[/bold] tarayıcısı kapatılıyor...", style="blue", box=box.ROUNDED))
    asyncio.run(close_all_browsers())
    console.print("[green]Tüm tarayıcı pencereleri kapatıldı.[/green]")


if __name__ == "__main__":
    app()