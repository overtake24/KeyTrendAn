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
                try:
                    # String değerleri sayısal değerlere dönüştürmeye çalışıyoruz
                    if isinstance(data, dict):
                        values = [float(val) if isinstance(val, (int, float, str)) and str(val).replace('.', '',
                                                                                                        1).isdigit() else 0
                                  for val in data.values()]

                        if values:
                            results["stats"][keyword] = {
                                "mean": np.mean(values),
                                "std": np.std(values),
                                "trend": "yükseliyor" if values[-1] > values[0] else "düşüyor"
                            }

                            # Basit tahminleme (son değerin %10 artışı)
                            last_value = values[-1]
                            results["predictions"][keyword] = [
                                last_value * 1.1,
                                last_value * 1.2,
                                last_value * 1.3
                            ]
                except Exception as e:
                    # Analiz sırasında hata oluşursa, hatayı kaydediyoruz
                    results["stats"][keyword] = {
                        "error": f"Analiz hatası: {str(e)}"
                    }

            elif source == "twitter":
                # Twitter verisi için basit analiz
                try:
                    tweet_count = len(data) if isinstance(data, list) else 0
                    results["stats"][keyword] = {
                        "tweet_count": tweet_count,
                        "engagement": tweet_count * 2.5  # Örnek bir ölçüm
                    }
                except Exception as e:
                    results["stats"][keyword] = {
                        "error": f"Twitter analiz hatası: {str(e)}"
                    }

        return results