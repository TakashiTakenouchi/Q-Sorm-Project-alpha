"""Generate test data for Q-Storm integration tests"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

def generate_sample_store_data(output_path='uploads/session_test_integration/test_data.csv'):
    """
    41列の小売データを生成
    恵比寿店・横浜元町店の2023年1月〜12月のデータ
    """
    np.random.seed(42)

    # 基本設定
    stores = ['恵比寿', '横浜元町']
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(365)]

    data = []

    for store in stores:
        for date in dates:
            # 売上金額（店舗と月で変動）
            base_sales = 500000 if store == '恵比寿' else 400000
            seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * date.month / 12)
            daily_sales = int(base_sales * seasonal_factor * (0.8 + 0.4 * np.random.random()))

            # 商品カテゴリ別売上（Mens_, Womens_等）
            mens_jackets = int(daily_sales * 0.15)
            mens_knit = int(daily_sales * 0.10)
            mens_pants = int(daily_sales * 0.12)
            womens_jackets = int(daily_sales * 0.18)
            womens_tops = int(daily_sales * 0.20)
            womens_pants = int(daily_sales * 0.15)
            womens_scarves = int(daily_sales * 0.10)

            # 粗利額
            gross_profit = int(daily_sales * (0.35 + 0.1 * np.random.random()))

            # 客数・客単価
            customer_count = int(100 + 50 * np.random.random())
            avg_transaction = daily_sales / customer_count if customer_count > 0 else 0

            row = {
                '店舗名': store,
                'shop': store,
                '年': date.year,
                '月': date.month,
                '日': date.day,
                '営業日付': date.strftime('%Y-%m-%d'),
                '売上金額': daily_sales,
                'Total_Sales': daily_sales,
                '粗利額': gross_profit,
                '粗利率': round(gross_profit / daily_sales * 100, 2) if daily_sales > 0 else 0,
                '売上数量': int(customer_count * 2.5),
                '客数': customer_count,
                '客単価': round(avg_transaction, 2),
                'Mens_JACKETS&OUTER2': mens_jackets,
                'Mens_KNIT': mens_knit,
                'Mens_PANTS': mens_pants,
                "WOMEN'S_JACKETS": womens_jackets,
                "WOMEN'S_TOPS": womens_tops,
                "WOMEN'S_PANTS": womens_pants,
                "WOMEN'S_SCARF & STOLES": womens_scarves,
                '坪売上': daily_sales / 100,
                '人時売上': daily_sales / 80,
                '在庫金額': int(daily_sales * 1.5),
            }

            # 残りの列を埋める（41列に合わせる）
            for i in range(len(row), 41):
                row[f'column_{i}'] = 0

            data.append(row)

    df = pd.DataFrame(data)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print(f"✅ テストデータ生成完了: {output_path}")
    print(f"   行数: {len(df)}")
    print(f"   列数: {len(df.columns)}")
    print(f"   期間: {df['営業日付'].min()} 〜 {df['営業日付'].max()}")
    print(f"   店舗: {df['店舗名'].unique().tolist()}")

    return str(output_path)

if __name__ == '__main__':
    generate_sample_store_data()
