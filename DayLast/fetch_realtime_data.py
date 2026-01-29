#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
実際のシェアサイクルAPIからリアルタイムデータを取得
東京のドコモ・バイクシェアデータを使用
"""

import requests
import pandas as pd
from datetime import datetime
import time

def fetch_citybikes_data():
    """CityBikes APIから東京＋近郊のシェアサイクルデータを取得"""
    NETWORK_IDS = [
        'docomo-cycle-tokyo',
        'hellocycling-tokyo'
    ]
    
    print("=" * 70)
    print("実際のシェアサイクルデータ取得中（東京23区のみ）...")
    print(f"対象ネットワーク: {', '.join(NETWORK_IDS)}")
    print("=" * 70)
    
    try:
        print("\n⏳ データ取得中（最大30秒）...")
        all_stations = []
        for network_id in NETWORK_IDS:
            api_url = f"http://api.citybik.es/v2/networks/{network_id}"
            try:
                resp = requests.get(api_url, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                stations = data['network']['stations']
                for st in stations:
                    st['__network_id'] = network_id
                all_stations.extend(stations)
            except requests.exceptions.RequestException as e:
                print(f"  ! 取得失敗: {network_id} ({e})")
                continue
        
        # 東京23区の概ねの範囲（緯度経度の簡易フィルタ）
        TOKYO23_BBOX = {
            "min_lat": 35.55,
            "max_lat": 35.82,
            "min_lon": 139.60,
            "max_lon": 139.92
        }

        filtered_stations = [
            st for st in all_stations
            if TOKYO23_BBOX["min_lat"] <= st["latitude"] <= TOKYO23_BBOX["max_lat"]
            and TOKYO23_BBOX["min_lon"] <= st["longitude"] <= TOKYO23_BBOX["max_lon"]
        ]

        print(f"✓ {len(all_stations)} ステーションのデータを取得")
        print(f"✓ 東京23区内フィルタ後: {len(filtered_stations)} ステーション")
        
        # DataFrameに変換
        records = []
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for st in filtered_stations:
            records.append({
                'timestamp': current_time,
                'station_name': st['name'],
                'free_bikes': st['free_bikes'],
                'latitude': st['latitude'],
                'longitude': st['longitude'],
                'empty_slots': st.get('empty_slots', 0),
                'extra': st.get('extra', {}),
                'network_id': st.get('__network_id', '')
            })
        
        df = pd.DataFrame(records)
        
        # bike_log.csvとして保存（上書き）
        csv_file = 'bike_log.csv'
        df[['timestamp', 'station_name', 'free_bikes', 'latitude', 'longitude']].to_csv(
            csv_file, index=False, encoding='utf-8'
        )
        
        print(f"\n✓ {csv_file} に保存しました")
        print(f"  取得時刻: {current_time}")
        print(f"  ステーション数: {len(df)}")
        print(f"  緯度範囲: {df['latitude'].min():.4f} ～ {df['latitude'].max():.4f}")
        print(f"  経度範囲: {df['longitude'].min():.4f} ～ {df['longitude'].max():.4f}")
        print(f"  利用可能台数: {df['free_bikes'].sum()} 台")
        print(f"  平均台数/ステーション: {df['free_bikes'].mean():.1f} 台")
        
        # 在庫状況の統計
        zero_bikes = len(df[df['free_bikes'] == 0])
        low_bikes = len(df[df['free_bikes'] <= 3])
        print(f"\n【在庫状況】")
        print(f"  0台: {zero_bikes} ({zero_bikes/len(df)*100:.1f}%)")
        print(f"  3台以下: {low_bikes} ({low_bikes/len(df)*100:.1f}%)")
        
        return df
        
    except requests.exceptions.Timeout:
        print("\n❌ タイムアウト: API応答がありません")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API取得エラー: {e}")
        return None
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return None

if __name__ == "__main__":
    df = fetch_citybikes_data()
    
    if df is not None:
        print("\n" + "=" * 70)
        print("完了！ bike_log.csv が実際のデータで更新されました")
        print("次のコマンドでクラスタ地図を生成してください:")
        print("  python cluster_dbscan_map.py")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("データ取得に失敗しました")
        print("ネットワーク接続またはAPI状態を確認してください")
        print("=" * 70)
