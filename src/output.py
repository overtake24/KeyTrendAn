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
            stats_table.add_column("Kaynak", style="magenta")
            stats_table.add_column("Metrik", style="green")
            stats_table.add_column("Değer", style="yellow")

            for keyword, stat in results["stats"].items():
                if "mean" in stat:  # Google Trends istatistikleri
                    stats_table.add_row(
                        keyword,
                        "Google Trends",
                        "Ortalama",
                        f"{stat['mean']:.2f}"
                    )
                    stats_table.add_row(
                        keyword,
                        "Google Trends",
                        "Std Sapma",
                        f"{stat['std']:.2f}"
                    )
                    stats_table.add_row(
                        keyword,
                        "Google Trends",
                        "Trend",
                        stat["trend"]
                    )
                elif "tweet_count" in stat:  # Twitter istatistikleri
                    stats_table.add_row(
                        keyword,
                        "Twitter",
                        "Tweet Sayısı",
                        f"{stat['tweet_count']}"
                    )
                    stats_table.add_row(
                        keyword,
                        "Twitter",
                        "Etkileşim",
                        f"{stat['engagement']:.1f}"
                    )
                elif "post_count" in stat and "avg_score" in stat:  # Reddit istatistikleri
                    stats_table.add_row(
                        keyword,
                        "Reddit",
                        "Post Sayısı",
                        f"{stat['post_count']}"
                    )
                    stats_table.add_row(
                        keyword,
                        "Reddit",
                        "Ort. Skor",
                        f"{stat['avg_score']:.1f}"
                    )
                    stats_table.add_row(
                        keyword,
                        "Reddit",
                        "Etkileşim İndeksi",
                        f"{stat['engagement_index']:.1f}"
                    )
                elif "hit_count" in stat:  # HackerNews istatistikleri
                    stats_table.add_row(
                        keyword,
                        "HackerNews",
                        "Hit Sayısı",
                        f"{stat['hit_count']}"
                    )
                    stats_table.add_row(
                        keyword,
                        "HackerNews",
                        "Ort. Puanlar",
                        f"{stat['avg_points']:.1f}"
                    )
                    stats_table.add_row(
                        keyword,
                        "HackerNews",
                        "Teknoloji İlgisi",
                        f"{stat['tech_relevance']:.1f}"
                    )
                elif "post_count" in stat and "avg_likes" in stat:  # Instagram istatistikleri
                    stats_table.add_row(
                        keyword,
                        "Instagram",
                        "Post Sayısı",
                        f"{stat['post_count']}"
                    )
                    stats_table.add_row(
                        keyword,
                        "Instagram",
                        "Ort. Beğeni",
                        f"{stat['avg_likes']:.1f}"
                    )
                    stats_table.add_row(
                        keyword,
                        "Instagram",
                        "Etkileşim Oranı",
                        f"{stat['engagement_rate']:.1f}"
                    )
                elif "error" in stat:  # Hata durumları
                    stats_table.add_row(
                        keyword,
                        "Error",
                        "Hata",
                        stat["error"]
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