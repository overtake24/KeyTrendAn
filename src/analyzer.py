import pandas as pd
import numpy as np
import json
from datetime import datetime


class Analyzer:
    def __init__(self, data):
        self.data = data

    def run_analysis(self):
        results = {
            "stats": {},
            "predictions": {},
            "cross_platform_insights": {}
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
                            # Son 30 gün trendi
                            trend_direction = "yükseliyor" if values[-1] > values[0] else "düşüyor"

                            # Trend gücü hesaplama
                            if len(values) > 1:
                                trend_strength = abs((values[-1] - values[0]) / max(values[0], 1)) * 100
                            else:
                                trend_strength = 0

                            results["stats"][keyword] = {
                                "source": "google_trends",
                                "mean": np.mean(values),
                                "std": np.std(values),
                                "trend": trend_direction,
                                "trend_strength": trend_strength,
                                "peak_value": max(values),
                                "current_value": values[-1],
                                "popularity_index": values[-1] / max(values) * 100 if max(values) > 0 else 0
                            }

                            # Basit tahminleme (ARIMA benzeri yaklaşım)
                            if len(values) >= 3:
                                # Son 3 değerden trend çıkar
                                last_values = values[-3:]
                                diff1 = last_values[1] - last_values[0]
                                diff2 = last_values[2] - last_values[1]
                                avg_diff = (diff1 + diff2) / 2

                                results["predictions"][keyword] = [
                                    last_values[2] + avg_diff,
                                    last_values[2] + avg_diff * 2,
                                    last_values[2] + avg_diff * 3
                                ]
                            else:
                                # Yeterli veri yoksa basit artış
                                last_value = values[-1]
                                results["predictions"][keyword] = [
                                    last_value * 1.1,
                                    last_value * 1.2,
                                    last_value * 1.3
                                ]
                except Exception as e:
                    # Analiz sırasında hata oluşursa, hatayı kaydediyoruz
                    results["stats"][keyword] = {
                        "source": "google_trends",
                        "error": f"Analiz hatası: {str(e)}"
                    }

            elif source == "twitter":
                # Twitter verisi için analiz
                try:
                    tweet_count = len(data) if isinstance(data, list) else 0

                    if tweet_count > 0:
                        # Metrikleri topla
                        total_likes = sum(
                            tweet.get("metrics", {}).get("like_count", 0) for tweet in data if isinstance(tweet, dict))
                        total_retweets = sum(tweet.get("metrics", {}).get("retweet_count", 0) for tweet in data if
                                             isinstance(tweet, dict))
                        total_replies = sum(
                            tweet.get("metrics", {}).get("reply_count", 0) for tweet in data if isinstance(tweet, dict))

                        # Metriklerden skor hesapla
                        engagement_score = (total_likes + total_retweets * 2 + total_replies * 3) / tweet_count

                        results["stats"][keyword] = {
                            "source": "twitter",
                            "tweet_count": tweet_count,
                            "avg_likes": total_likes / tweet_count if tweet_count > 0 else 0,
                            "avg_retweets": total_retweets / tweet_count if tweet_count > 0 else 0,
                            "avg_replies": total_replies / tweet_count if tweet_count > 0 else 0,
                            "engagement_score": engagement_score,
                            "viral_potential": total_retweets / (total_likes + 1) * 100  # Viral potansiyel göstergesi
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "twitter",
                            "tweet_count": 0,
                            "engagement_score": 0,
                            "viral_potential": 0
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "twitter",
                        "error": f"Twitter analiz hatası: {str(e)}"
                    }

            elif source == "reddit":
                # Reddit verisi için analiz
                try:
                    post_count = len(data) if isinstance(data, list) else 0

                    if post_count > 0:
                        avg_score = sum(post.get("score", 0) for post in data) / post_count
                        avg_comments = sum(post.get("comments", 0) for post in data) / post_count

                        # Topluluk katılım oranı
                        community_engagement = avg_comments / avg_score if avg_score > 0 else 0

                        results["stats"][keyword] = {
                            "source": "reddit",
                            "post_count": post_count,
                            "avg_score": avg_score,
                            "avg_comments": avg_comments,
                            "community_engagement": community_engagement,
                            "discussion_index": (avg_score + avg_comments * 2) / 3,  # Tartışma endeksi
                            "community_interest": post_count * avg_score / 100  # Topluluk ilgisi
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "reddit",
                            "post_count": 0,
                            "discussion_index": 0,
                            "community_interest": 0
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "reddit",
                        "error": f"Reddit analiz hatası: {str(e)}"
                    }

            elif source == "hackernews":
                # HackerNews verisi için analiz
                try:
                    hit_count = len(data) if isinstance(data, list) else 0

                    if hit_count > 0:
                        avg_points = sum(hit.get("points", 0) for hit in data) / hit_count
                        avg_comments = sum(hit.get("num_comments", 0) for hit in data) / hit_count

                        # Teknolojik ilgi endeksi
                        tech_relevance = (avg_points / (avg_comments + 1)) * 10

                        results["stats"][keyword] = {
                            "source": "hackernews",
                            "hit_count": hit_count,
                            "avg_points": avg_points,
                            "avg_comments": avg_comments,
                            "tech_relevance": tech_relevance,
                            "discussion_quality": (avg_comments * avg_points) / 100,  # Tartışma kalitesi
                            "developer_interest": avg_points * hit_count / 10  # Geliştirici ilgisi
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "hackernews",
                            "hit_count": 0,
                            "tech_relevance": 0,
                            "developer_interest": 0
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "hackernews",
                        "error": f"HackerNews analiz hatası: {str(e)}"
                    }

            elif source == "instagram":
                # Instagram verisi için analiz
                try:
                    post_count = len(data) if isinstance(data, list) else 0

                    if post_count > 0:
                        avg_likes = sum(post.get("likes_count", 0) for post in data) / post_count
                        avg_comments = sum(post.get("comments_count", 0) for post in data) / post_count

                        # Post türüne göre dağılım
                        types = {}
                        for post in data:
                            post_type = post.get("type", "unknown")
                            types[post_type] = types.get(post_type, 0) + 1

                        # Görsel trendler skoru
                        visual_trend_score = avg_likes * (post_count ** 0.5) / 100

                        results["stats"][keyword] = {
                            "source": "instagram",
                            "post_count": post_count,
                            "avg_likes": avg_likes,
                            "avg_comments": avg_comments,
                            "engagement_rate": (avg_likes + avg_comments * 2) / post_count,
                            "post_type_distribution": types,
                            "visual_trend_score": visual_trend_score,
                            "social_visibility": (avg_likes ** 0.7) * (post_count ** 0.3)  # Sosyal görünürlük
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "instagram",
                            "post_count": 0,
                            "engagement_rate": 0,
                            "visual_trend_score": 0
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "instagram",
                        "error": f"Instagram analiz hatası: {str(e)}"
                    }

            elif source == "youtube":
                # YouTube verisi için analiz
                try:
                    video_count = len(data) if isinstance(data, list) else 0

                    if video_count > 0:
                        avg_views = sum(video.get("view_count", 0) for video in data) / video_count
                        avg_likes = sum(video.get("like_count", 0) for video in data) / video_count
                        avg_comments = sum(video.get("comment_count", 0) for video in data) / video_count

                        # Video etkileşim oranı
                        engagement_ratio = (avg_likes + avg_comments) / avg_views if avg_views > 0 else 0

                        results["stats"][keyword] = {
                            "source": "youtube",
                            "video_count": video_count,
                            "avg_views": avg_views,
                            "avg_likes": avg_likes,
                            "avg_comments": avg_comments,
                            "engagement_ratio": engagement_ratio,
                            "popularity_score": (avg_views + avg_likes * 10) / 2,  # Video popülerlik skoru
                            "content_interest": (video_count * avg_views) / 1000  # İçerik ilgisi
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "youtube",
                            "video_count": 0,
                            "engagement_ratio": 0,
                            "popularity_score": 0
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "youtube",
                        "error": f"YouTube analiz hatası: {str(e)}"
                    }

            elif source == "news":
                # Haber verisi için analiz
                try:
                    article_count = len(data) if isinstance(data, list) else 0

                    if article_count > 0:
                        # Duygu analizi dağılımı
                        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
                        for article in data:
                            sentiment = article.get("sentiment", "neutral")
                            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

                        # Duygu skoru (-100 ile 100 arası)
                        sentiment_score = ((sentiment_counts.get("positive", 0) - sentiment_counts.get("negative", 0)) /
                                           article_count) * 100

                        # Kaynak çeşitliliği
                        sources = set(article.get("source", "") for article in data)
                        source_diversity = len(sources) / article_count * 10

                        results["stats"][keyword] = {
                            "source": "news",
                            "article_count": article_count,
                            "sentiment_distribution": sentiment_counts,
                            "sentiment_score": sentiment_score,
                            "source_diversity": source_diversity,
                            "media_attention": article_count * (
                                        sum(article.get("relevance_score", 0.5) for article in data) / article_count),
                            "trending_status": "high" if article_count > 10 else "medium" if article_count > 5 else "low"
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "news",
                            "article_count": 0,
                            "sentiment_score": 0,
                            "trending_status": "none"
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "news",
                        "error": f"News analiz hatası: {str(e)}"
                    }

            elif source == "pinterest":
                # Pinterest verisi için analiz
                try:
                    pin_count = len(data) if isinstance(data, list) else 0

                    if pin_count > 0:
                        avg_saves = sum(pin.get("save_count", 0) for pin in data) / pin_count
                        avg_clicks = sum(pin.get("link_clicks", 0) for pin in data) / pin_count

                        # Kategori popülerliği
                        categories = {}
                        for pin in data:
                            category = pin.get("category", "other")
                            categories[category] = categories.get(category, 0) + 1

                        top_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "none"

                        results["stats"][keyword] = {
                            "source": "pinterest",
                            "pin_count": pin_count,
                            "avg_saves": avg_saves,
                            "avg_clicks": avg_clicks,
                            "click_save_ratio": avg_clicks / avg_saves if avg_saves > 0 else 0,
                            "category_distribution": categories,
                            "top_category": top_category,
                            "inspiration_score": avg_saves * (pin_count ** 0.5) / 10  # İlham vericilik skoru
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "pinterest",
                            "pin_count": 0,
                            "click_save_ratio": 0,
                            "inspiration_score": 0
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "pinterest",
                        "error": f"Pinterest analiz hatası: {str(e)}"
                    }

            elif source == "linkedin":
                # LinkedIn verisi için analiz
                try:
                    post_count = len(data) if isinstance(data, list) else 0

                    if post_count > 0:
                        # Engagement hesapla
                        total_likes = sum(post.get("engagement", {}).get("likes", 0) for post in data)
                        total_comments = sum(post.get("engagement", {}).get("comments", 0) for post in data)
                        total_shares = sum(post.get("engagement", {}).get("shares", 0) for post in data)

                        avg_likes = total_likes / post_count
                        avg_comments = total_comments / post_count
                        avg_shares = total_shares / post_count

                        # Endüstri analizi
                        industries = {}
                        for post in data:
                            industry = post.get("industry_relevance", "general")
                            industries[industry] = industries.get(industry, 0) + 1

                        top_industry = max(industries.items(), key=lambda x: x[1])[0] if industries else "none"

                        results["stats"][keyword] = {
                            "source": "linkedin",
                            "post_count": post_count,
                            "avg_likes": avg_likes,
                            "avg_comments": avg_comments,
                            "avg_shares": avg_shares,
                            "professional_engagement": (avg_comments * 2 + avg_shares * 3) / 5,
                            "industry_distribution": industries,
                            "top_industry": top_industry,
                            "b2b_relevance": (post_count * avg_shares) / 10  # B2B ilgi endeksi
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "linkedin",
                            "post_count": 0,
                            "professional_engagement": 0,
                            "b2b_relevance": 0
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "linkedin",
                        "error": f"LinkedIn analiz hatası: {str(e)}"
                    }

            elif source == "amazon":
                # Amazon verisi için analiz
                try:
                    product_count = len(data) if isinstance(data, list) else 0

                    if product_count > 0:
                        avg_price = sum(product.get("price", 0) for product in data) / product_count
                        avg_rating = sum(product.get("rating", 0) for product in data) / product_count
                        avg_reviews = sum(product.get("review_count", 0) for product in data) / product_count

                        # İndirim oranı
                        discount_rates = []
                        for product in data:
                            if product.get("old_price") and product.get("price"):
                                discount = (product["old_price"] - product["price"]) / product["old_price"] * 100
                                discount_rates.append(discount)

                        avg_discount = sum(discount_rates) / len(discount_rates) if discount_rates else 0

                        # Kategori analizi
                        categories = {}
                        for product in data:
                            category = product.get("category", "other")
                            categories[category] = categories.get(category, 0) + 1

                        top_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "none"

                        results["stats"][keyword] = {
                            "source": "amazon",
                            "product_count": product_count,
                            "avg_price": avg_price,
                            "avg_rating": avg_rating,
                            "avg_reviews": avg_reviews,
                            "avg_discount": avg_discount,
                            "product_popularity": avg_reviews * avg_rating,
                            "category_distribution": categories,
                            "top_category": top_category,
                            "commercial_potential": (avg_reviews ** 0.7) * (avg_rating ** 0.3) * (
                                        100 - avg_discount) / 100
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "amazon",
                            "product_count": 0,
                            "avg_price": 0,
                            "product_popularity": 0
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "amazon",
                        "error": f"Amazon analiz hatası: {str(e)}"
                    }

            elif source == "ebay":
                # eBay verisi için analiz
                try:
                    listing_count = len(data) if isinstance(data, list) else 0

                    if listing_count > 0:
                        avg_price = sum(listing.get("price", 0) for listing in data) / listing_count
                        avg_shipping = sum(listing.get("shipping", 0) for listing in data) / listing_count

                        # İlan türü dağılımı
                        listing_types = {}
                        for listing in data:
                            listing_type = listing.get("listing_type", "unknown")
                            listing_types[listing_type] = listing_types.get(listing_type, 0) + 1

                        # Ürün durumu dağılımı
                        conditions = {}
                        for listing in data:
                            condition = listing.get("condition", "unknown")
                            conditions[condition] = conditions.get(condition, 0) + 1

                        results["stats"][keyword] = {
                            "source": "ebay",
                            "listing_count": listing_count,
                            "avg_price": avg_price,
                            "avg_shipping": avg_shipping,
                            "total_cost": avg_price + avg_shipping,
                            "listing_type_distribution": listing_types,
                            "condition_distribution": conditions,
                            "auction_ratio": listing_types.get("Auction",
                                                               0) / listing_count if listing_count > 0 else 0,
                            "market_liquidity": listing_count / (avg_price + 1) * 10  # Pazar likiditesi
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "ebay",
                            "listing_count": 0,
                            "avg_price": 0,
                            "market_liquidity": 0
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "ebay",
                        "error": f"eBay analiz hatası: {str(e)}"
                    }

            elif source == "otto":
                # Otto verisi için analiz
                try:
                    product_count = len(data) if isinstance(data, list) else 0

                    if product_count > 0:
                        avg_price = sum(product.get("price", 0) for product in data) / product_count
                        avg_rating = sum(product.get("rating", 0) for product in data) / product_count

                        # İndirim oranı
                        discount_items = 0
                        total_discount = 0
                        for product in data:
                            if product.get("sale_price") and product.get("price"):
                                discount_items += 1
                                discount = (product["price"] - product["sale_price"]) / product["price"] * 100
                                total_discount += discount

                        avg_discount = total_discount / discount_items if discount_items > 0 else 0
                        discount_ratio = discount_items / product_count

                        # Kategori analizi
                        categories = {}
                        for product in data:
                            category = product.get("category", "other")
                            categories[category] = categories.get(category, 0) + 1

                        results["stats"][keyword] = {
                            "source": "otto",
                            "product_count": product_count,
                            "avg_price": avg_price,
                            "avg_rating": avg_rating,
                            "avg_discount": avg_discount,
                            "discount_product_ratio": discount_ratio,
                            "category_distribution": categories,
                            "german_market_index": product_count * avg_rating / (avg_price + 1) * 10
                        }
                    else:
                        results["stats"][keyword] = {
                            "source": "otto",
                            "product_count": 0,
                            "avg_price": 0,
                            "german_market_index": 0
                        }
                except Exception as e:
                    results["stats"][keyword] = {
                        "source": "otto",
                        "error": f"Otto analiz hatası: {str(e)}"
                    }

        # Cross-platform insights (tüm kaynakları karşılaştır)
        try:
            keyword_sources = {}

            # Anahtar kelime başına tüm kaynakları topla
            for entry in self.data:
                keyword = entry["keyword"]
                source = entry["source"]

                if keyword not in keyword_sources:
                    keyword_sources[keyword] = []

                keyword_sources[keyword].append(source)

            # Her anahtar kelime için platform karşılaştırması yap
            for keyword, sources in keyword_sources.items():
                source_count = len(sources)

                if source_count > 1:
                    source_insights = {}

                    # Her kaynak için temel metrikler
                    for source in sources:
                        if source == "google_trends":
                            source_insights["search_interest"] = results["stats"].get(keyword, {}).get("current_value",
                                                                                                       0)
                        elif source in ["twitter", "reddit", "instagram", "linkedin"]:
                            source_insights[f"{source}_engagement"] = results["stats"].get(keyword, {}).get(
                                "engagement_rate", 0)
                        elif source in ["amazon", "ebay", "otto"]:
                            source_insights[f"{source}_commercial"] = results["stats"].get(keyword, {}).get(
                                "product_count", 0)

                    # Platform karşılaştırma skoru
                    cross_platform_score = sum(source_insights.values()) / len(
                        source_insights) if source_insights else 0

                    results["cross_platform_insights"][keyword] = {
                        "platforms": sources,
                        "metrics": source_insights,
                        "cross_platform_score": cross_platform_score,
                        "trend_strength": "strong" if cross_platform_score > 100 else "medium" if cross_platform_score > 50 else "weak",
                        "recommendation": "trending up" if cross_platform_score > 75 else "stable" if cross_platform_score > 25 else "trending down"
                    }
        except Exception as e:
            results["cross_platform_insights"]["error"] = str(e)

        return results