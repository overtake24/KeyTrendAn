import pandas as pd
import numpy as np
import json


class Analyzer:
    def __init__(self, data):
        self.data = data

    def run_analysis(self):
        results = {
            "stats": {},
            "predictions": {}
        }

        # Anahtar kelime başına istatistikler
        for entry in self.data:
            keyword = entry["keyword"]
            source = entry["source"]
            data = entry["data"]

            if source == "google_trends":
                # Google Trends verisi için analiz
                values = list(data.values())

                results["stats"][keyword] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "trend": "yükseliyor" if values[-1] > values[0] else "düşüyor"
                }

                # Basit tahminleme (son değerin %10 artışı)
                # İleride ARIMA gibi modeller eklenecek
                last_value = values[-1]
                results["predictions"][keyword] = [
                    last_value * 1.1,
                    last_value * 1.2,
                    last_value * 1.3
                ]

            elif source == "twitter":
                # Twitter verisi için basit analiz
                tweet_count = len(data)
                results["stats"][keyword] = {
                    "tweet_count": tweet_count,
                    "engagement": tweet_count * 2.5  # Örnek bir ölçüm
                }

        return results