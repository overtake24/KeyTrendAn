import json
from rich.console import Console
from rich.table import Table


class OutputManager:
    def __init__(self, format="terminal"):
        self.format = format
        self.console = Console()

    def display(self, results):
        if self.format == "terminal":
            self._display_terminal(results)
        elif self.format == "json":
            self._display_json(results)
        else:
            self.console.print(f"[red]Bilinmeyen format: {self.format}[/red]")

    def _display_terminal(self, results):
        if "stats" in results:
            # İstatistik tablosu
            stats_table = Table(title="İstatistikler")
            stats_table.add_column("Anahtar Kelime", style="cyan")
            stats_table.add_column("Ortalama", style="green")
            stats_table.add_column("Std Sapma", style="yellow")
            stats_table.add_column("Trend", style="magenta")

            for keyword, stat in results["stats"].items():
                if "mean" in stat:  # Google Trends istatistikleri
                    stats_table.add_row(
                        keyword,
                        f"{stat['mean']:.2f}",
                        f"{stat['std']:.2f}",
                        stat["trend"]
                    )
                elif "tweet_count" in stat:  # Twitter istatistikleri
                    stats_table.add_row(
                        keyword,
                        f"{stat['tweet_count']} tweets",
                        "N/A",
                        f"Engagement: {stat['engagement']:.1f}"
                    )

            self.console.print(stats_table)

        if "predictions" in results:
            # Tahminleme tablosu
            pred_table = Table(title="Tahminler")
            pred_table.add_column("Anahtar Kelime", style="cyan")
            pred_table.add_column("3 Adımlık Tahmin", style="green")

            for keyword, pred in results["predictions"].items():
                pred_table.add_row(keyword, ", ".join([f"{p:.2f}" for p in pred]))

            self.console.print(pred_table)

    def _display_json(self, results):
        print(json.dumps(results, indent=2))

    def save_to_file(self, results, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        self.console.print(f"[green]Sonuçlar {filename} dosyasına kaydedildi![/green]")