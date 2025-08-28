"""
JRA-VAN DataLab メインプログラム
競馬データの取得・管理を行うメインスクリプト

Usage:
    python main_jra_van.py --setup    # 初回セットアップ
    python main_jra_van.py --update   # 差分更新
    python main_jra_van.py --realtime # リアルタイムデータ取得
"""

import argparse
import logging
import sys
from datetime import datetime

from jravan.manager import JVDataManager
from jravan.client import JVLinkClient

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jravan.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def setup_database():
    """初回セットアップ（基本データ取得）"""
    print("=" * 70)
    print("JRA-VAN DataLab 初回セットアップ")
    print("=" * 70)
    print("このプロセスは大量のデータをダウンロードします。")
    print("完了まで数時間かかる可能性があります。")
    print()
    
    response = input("セットアップを開始しますか？ (y/n): ")
    if response.lower() != 'y':
        print("セットアップをキャンセルしました。")
        return
    
    manager = JVDataManager()
    
    try:
        # 各種データのセットアップ
        data_specs = [
            ("YSCH", "年間スケジュール"),
            ("RACE", "レース情報"),
            ("HOSE", "競走馬データ"),
        ]
        
        for spec, description in data_specs:
            print(f"\n{description}を取得中...")
            success = manager.download_setup_data(spec)
            
            if not success:
                logger.error(f"{description}の取得に失敗しました")
                return
        
        print("\n" + "=" * 70)
        print("セットアップが完了しました！")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"セットアップエラー: {e}")
        
    finally:
        manager.close()


def update_database(from_date: str = None):
    """差分データ更新"""
    print("=" * 70)
    print("JRA-VAN DataLab データ更新")
    print("=" * 70)
    
    manager = JVDataManager()
    
    try:
        print("差分データを取得中...")
        success = manager.update_data(from_date, "DIFF")
        
        if success:
            print("\n更新が完了しました！")
        else:
            logger.error("更新に失敗しました")
            
    except Exception as e:
        logger.error(f"更新エラー: {e}")
        
    finally:
        manager.close()


def get_realtime_data():
    """リアルタイムデータ取得"""
    print("=" * 70)
    print("JRA-VAN DataLab リアルタイムデータ取得")
    print("=" * 70)
    
    manager = JVDataManager()
    
    try:
        # 取得するデータ種別
        realtime_specs = [
            (JVLinkClient.REALTIME_SPEC['WEIGHT'], "馬体重"),
            (JVLinkClient.REALTIME_SPEC['ODDS_WIN_PLACE'], "単複オッズ"),
            (JVLinkClient.REALTIME_SPEC['RESULT'], "速報成績"),
        ]
        
        for spec, description in realtime_specs:
            print(f"\n{description}を取得中...")
            success = manager.get_realtime_data(spec)
            
            if not success:
                logger.warning(f"{description}の取得に失敗しました")
        
        print("\nリアルタイムデータ取得が完了しました！")
        
    except Exception as e:
        logger.error(f"リアルタイムエラー: {e}")
        
    finally:
        manager.close()


def test_connection():
    """接続テスト"""
    print("=" * 70)
    print("JRA-VAN DataLab 接続テスト")
    print("=" * 70)
    
    client = JVLinkClient()
    
    try:
        # 初期化
        ret = client.initialize("TEST")
        
        if ret == 0:
            print(f"○ 接続成功")
            print(f"  JV-Linkバージョン: {client.get_version()}")
            
            # 設定ダイアログ表示（オプション）
            response = input("\n設定ダイアログを表示しますか？ (y/n): ")
            if response.lower() == 'y':
                client.set_ui_properties()
            
            print("\n接続テストが成功しました！")
            
        else:
            print(f"× 接続失敗")
            print(f"  エラー: {client.get_error_message(ret)}")
            
            if ret == -211:
                print("\n以下を確認してください：")
                print("1. JRA-VAN DataLabに契約済みか")
                print("2. JV-Link.exeが正しく登録されているか")
                print("3. サービスキーが有効か")
                
    except Exception as e:
        logger.error(f"接続テストエラー: {e}")
        
    finally:
        client.close()


def show_statistics():
    """データベース統計情報表示"""
    print("=" * 70)
    print("JRA-VAN DataLab データベース統計")
    print("=" * 70)
    
    import sqlite3
    
    try:
        conn = sqlite3.connect("jravan.db")
        cursor = conn.cursor()
        
        # 各テーブルのレコード数
        tables = [
            ("races", "レース"),
            ("results", "馬毎レース情報"),
            ("horses", "競走馬"),
            ("odds", "オッズ"),
            ("weights", "馬体重"),
            ("schedules", "スケジュール"),
        ]
        
        print("\n【レコード数】")
        for table, description in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {description:20s}: {count:,}件")
        
        # 最新レース日
        cursor.execute("""
            SELECT MAX(year || '/' || SUBSTR(monthday, 1, 2) || '/' || SUBSTR(monthday, 3, 2))
            FROM races
        """)
        latest_date = cursor.fetchone()[0]
        if latest_date:
            print(f"\n【最新レース日】")
            print(f"  {latest_date}")
        
        # 処理履歴
        cursor.execute("""
            SELECT process_type, data_spec, finished_at, processed_count, error_count
            FROM process_history
            WHERE status = 'SUCCESS'
            ORDER BY finished_at DESC
            LIMIT 5
        """)
        
        print(f"\n【最近の処理履歴】")
        for row in cursor.fetchall():
            process_type, data_spec, finished_at, processed, errors = row
            print(f"  {finished_at}: {process_type} {data_spec} (処理{processed}件, エラー{errors}件)")
        
        conn.close()
        
    except sqlite3.OperationalError:
        print("データベースが見つかりません。")
        print("先に --setup を実行してください。")
        
    except Exception as e:
        logger.error(f"統計表示エラー: {e}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='JRA-VAN DataLab データ管理プログラム'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='接続テストを実行'
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='初回セットアップ（基本データ取得）'
    )
    
    parser.add_argument(
        '--update',
        action='store_true',
        help='差分データ更新'
    )
    
    parser.add_argument(
        '--from-date',
        type=str,
        help='更新開始日（YYYYMMDD形式）'
    )
    
    parser.add_argument(
        '--realtime',
        action='store_true',
        help='リアルタイムデータ取得'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='データベース統計情報表示'
    )
    
    args = parser.parse_args()
    
    # 引数がない場合はヘルプ表示
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n使用例:")
        print("  python main_jra_van.py --test      # 接続テスト")
        print("  python main_jra_van.py --setup     # 初回セットアップ")
        print("  python main_jra_van.py --update    # 差分更新")
        print("  python main_jra_van.py --realtime  # リアルタイムデータ取得")
        print("  python main_jra_van.py --stats     # 統計情報表示")
        return
    
    # コマンド実行
    try:
        if args.test:
            test_connection()
        elif args.setup:
            setup_database()
        elif args.update:
            update_database(args.from_date)
        elif args.realtime:
            get_realtime_data()
        elif args.stats:
            show_statistics()
            
    except KeyboardInterrupt:
        print("\n\n処理を中断しました。")
        
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()