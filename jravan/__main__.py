"""
JRA-VAN Client メインエントリーポイント

使用方法:
    python -m jravan [オプション]
    jravan [オプション]  # pip install後
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加（開発時用）
sys.path.insert(0, str(Path(__file__).parent.parent))

from jravan.manager import JVDataManager
from jravan.client import JVLinkClient


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description='JRA-VAN DataLab Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 接続テスト
  jravan --test
  
  # 初期データ取得（セットアップ）
  jravan --setup
  
  # データ更新
  jravan --update
  
  # 統計情報表示
  jravan --stats
        """
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='JRA-VAN接続テストを実行'
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='初期データ取得（初回実行時）'
    )
    
    parser.add_argument(
        '--update',
        action='store_true',
        help='差分データ更新'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='データベース統計情報表示'
    )
    
    parser.add_argument(
        '--data-spec',
        default='RACE',
        choices=['RACE', 'DIFF', 'BLOD', 'MING', 'SNAP', 'YSCH'],
        help='取得するデータ種別（デフォルト: RACE）'
    )
    
    parser.add_argument(
        '--db',
        default='jravan.db',
        help='SQLiteデータベースファイル（デフォルト: jravan.db）'
    )
    
    parser.add_argument(
        '--save-path',
        default='jvdata',
        help='JV-Dataファイル保存先（デフォルト: jvdata）'
    )
    
    args = parser.parse_args()
    
    # 引数が何もない場合はヘルプ表示
    if not any([args.test, args.setup, args.update, args.stats]):
        parser.print_help()
        return 0
    
    # 接続テスト
    if args.test:
        print("JRA-VAN接続テスト開始...")
        print("="*50)
        
        client = JVLinkClient()
        ret = client.initialize("TEST")
        
        if ret == 0:
            print("✅ 接続成功！")
            print(f"JV-Linkバージョン: {client.get_version()}")
        else:
            print(f"❌ 接続エラー: {client.get_error_message(ret)}")
            if ret == -211:
                print("→ JRA-VANサービスキーの設定が必要です")
        
        client.close()
        return 0 if ret == 0 else 1
    
    # データマネージャー初期化
    with JVDataManager(args.db, args.save_path) as manager:
        
        # セットアップ
        if args.setup:
            print(f"初期データ取得開始: {args.data_spec}")
            print("※数時間かかる場合があります")
            success = manager.download_setup_data(args.data_spec)
            return 0 if success else 1
        
        # 更新
        if args.update:
            print("差分データ更新開始...")
            success = manager.update_data(data_spec=args.data_spec)
            return 0 if success else 1
        
        # 統計情報
        if args.stats:
            print("データベース統計情報:")
            print("="*50)
            
            import sqlite3
            conn = sqlite3.connect(args.db)
            cursor = conn.cursor()
            
            # 各テーブルの件数を取得
            tables = [
                ('races', 'レース'),
                ('results', 'レース結果'),
                ('horses', '競走馬'),
                ('odds', 'オッズ'),
                ('weights', '馬体重'),
                ('schedules', 'スケジュール'),
            ]
            
            for table_name, description in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"{description:15} : {count:,} 件")
                except:
                    print(f"{description:15} : - (未作成)")
            
            conn.close()
            return 0
    
    return 0


if __name__ == '__main__':
    sys.exit(main())