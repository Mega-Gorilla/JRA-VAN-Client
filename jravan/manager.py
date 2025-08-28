"""
JV-Data Manager Module
データの取得、解析、保存を管理するモジュール

Based on JRA-VAN SDK Ver4.9.0.2
"""

import sqlite3
import time
import os
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime, timedelta
import logging
from contextlib import contextmanager, closing

from .client import JVLinkClient
from .parser import RecordParser, CodeMaster

# ロギング設定
logger = logging.getLogger(__name__)


class JVDataManager:
    """JV-Dataの取得と保存を管理するクラス"""
    
    def __init__(self, db_path: str = "jravan.db", save_path: str = "jvdata"):
        """
        初期化
        
        Args:
            db_path: SQLiteデータベースパス
            save_path: JV-Dataファイル保存先パス
        """
        self.db_path = db_path
        self.save_path = save_path
        self.jvlink = JVLinkClient()
        self.conn = None
        self._connection_pool_size = 5  # パフォーマンス向上のため
        
        # ディレクトリ作成
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        # データベース初期化
        self.setup_database()
    
    def setup_database(self):
        """データベース初期設定"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
        
        # レーステーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS races (
                race_key TEXT PRIMARY KEY,
                year TEXT,
                monthday TEXT,
                jyo_code TEXT,
                jyo_name TEXT,
                kaiji INTEGER,
                nichiji INTEGER,
                race_num INTEGER,
                race_name TEXT,
                fukusho_name TEXT,
                grade_cd TEXT,
                syubetsu_cd TEXT,
                kyori INTEGER,
                track_cd TEXT,
                track_name TEXT,
                tenko_cd TEXT,
                tenko TEXT,
                shiba_baba_cd TEXT,
                shiba_baba TEXT,
                dirt_baba_cd TEXT,
                dirt_baba TEXT,
                hassotime TEXT,
                toroku_tosu INTEGER,
                syusso_tosu INTEGER,
                data_kubun TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 馬毎レース情報テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_key TEXT,
                umaban INTEGER,
                ketto_num TEXT,
                bamei TEXT,
                seibetsu_cd TEXT,
                barei INTEGER,
                keiro_cd TEXT,
                jockey_code TEXT,
                jockey_name TEXT,
                jockey_name_ryaku TEXT,
                trainer_code TEXT,
                trainer_name TEXT,
                trainer_syozoku TEXT,
                futan INTEGER,
                bataijyu INTEGER,
                zogen TEXT,
                kakutei_jyuni INTEGER,
                time TEXT,
                chakusa TEXT,
                tansho_odds REAL,
                ninsiki INTEGER,
                honsyo INTEGER,
                fukasyo INTEGER,
                data_kubun TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(race_key) REFERENCES races(race_key),
                UNIQUE(race_key, umaban)
            )
        """)
        
        # 競走馬マスタテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS horses (
                ketto_num TEXT PRIMARY KEY,
                bamei TEXT,
                birth_date TEXT,
                seibetsu_cd TEXT,
                hinsyu_cd TEXT,
                keiro_cd TEXT,
                keito TEXT,
                father TEXT,
                mother TEXT,
                bms TEXT,
                tozai_cd TEXT,
                trainer_code TEXT,
                trainer_name TEXT,
                banushi_code TEXT,
                banushi_name TEXT,
                breeder_code TEXT,
                breeder_name TEXT,
                sanchi_name TEXT,
                del_kubun TEXT,
                data_kubun TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # オッズテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS odds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_key TEXT,
                umaban INTEGER,
                tansho_odds INTEGER,
                fukusho_odds_low INTEGER,
                fukusho_odds_high INTEGER,
                tansho_ninki INTEGER,
                fukusho_ninki INTEGER,
                data_kubun TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(race_key) REFERENCES races(race_key),
                UNIQUE(race_key, umaban)
            )
        """)
        
        # 馬体重テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_key TEXT,
                umaban INTEGER,
                bataijyu INTEGER,
                zogen_fuka TEXT,
                zogen TEXT,
                data_kubun TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(race_key) REFERENCES races(race_key),
                UNIQUE(race_key, umaban)
            )
        """)
        
        # 年間スケジュールテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year TEXT,
                kaiji_date TEXT,
                jyo_code TEXT,
                jyo_name TEXT,
                kaiji INTEGER,
                nichiji INTEGER,
                youbi TEXT,
                henko_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, kaiji_date, jyo_code, kaiji, nichiji)
            )
        """)
        
        # 処理履歴テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_type TEXT,
                data_spec TEXT,
                from_time TEXT,
                to_time TEXT,
                read_count INTEGER,
                download_count INTEGER,
                processed_count INTEGER,
                error_count INTEGER,
                status TEXT,
                started_at TIMESTAMP,
                finished_at TIMESTAMP
            )
        """)
        
            # インデックス作成
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_race_date ON races(year, monthday)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_race_jyo ON races(jyo_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_result_ketto ON results(ketto_num)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_result_jockey ON results(jockey_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_result_trainer ON results(trainer_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_horse_father ON horses(father)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_horse_mother ON horses(mother)")
            
            conn.commit()
            logger.info("データベース初期化完了")
    
    def __enter__(self):
        """コンテキストマネージャー: エントリー"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了処理"""
        self.close()
        return False
    
    @contextmanager
    def get_db_connection(self) -> Iterator[sqlite3.Connection]:
        """
        データベース接続のコンテキストマネージャー
        
        Yields:
            sqlite3.Connection: データベース接続
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path, 
                timeout=30.0,  # タイムアウト設定
                check_same_thread=False  # スレッドセーフ
            )
            # パフォーマンス改善のための設定
            conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
            conn.execute('PRAGMA synchronous=NORMAL')  # 同期モード調整
            conn.execute('PRAGMA cache_size=10000')  # キャッシュサイズ増加
            conn.execute('PRAGMA temp_store=memory')  # 一時ファイルをメモリに保存
            conn.row_factory = sqlite3.Row  # 行を辞書風にアクセス可能に
            yield conn
        except sqlite3.Error as e:
            logger.error(f"データベースエラー: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def initialize_jvlink(self, sid: str = "UNKNOWN") -> bool:
        """
        JV-Link初期化
        
        Args:
            sid: ソフトウェアID
            
        Returns:
            成功時True
        """
        ret = self.jvlink.initialize(sid)
        if ret != 0:
            logger.error(f"JV-Link初期化エラー: {self.jvlink.get_error_message(ret)}")
            return False
        
        # 保存パス設定
        self.jvlink.set_save_path(self.save_path)
        self.jvlink.set_save_flag(1)  # ファイル保存有効
        
        return True
    
    def download_setup_data(self, data_spec: str = "RACE") -> bool:
        """
        セットアップデータ取得（初回実行時）
        
        Args:
            data_spec: データ種別
            
        Returns:
            成功時True
        """
        logger.info(f"セットアップデータ取得開始: {data_spec}")
        
        # 処理履歴記録開始
        process_id = self.start_process_history("SETUP", data_spec, "99999999999999")
        
        try:
            # JV-Link初期化
            if not self.initialize_jvlink():
                return False
            
            # セットアップデータ取得（オプション=3）
            ret, read_count, download_count, last_timestamp = self.jvlink.open(
                data_spec=data_spec,
                from_time="99999999999999",
                option=3  # セットアップデータ
            )
            
            if ret < 0:
                logger.error(f"JVOpenエラー: {self.jvlink.get_error_message(ret)}")
                self.finish_process_history(process_id, "ERROR", 0, 0)
                return False
            
            logger.info(f"読込対象: {read_count}件, ダウンロード: {download_count}ファイル")
            
            # データ読み込みと保存
            processed, errors = self.process_data(max_records=read_count)
            
            # 処理履歴更新
            self.finish_process_history(process_id, "SUCCESS", processed, errors)
            
            logger.info(f"セットアップ完了: 処理{processed}件, エラー{errors}件")
            return True
            
        except Exception as e:
            logger.error(f"セットアップエラー: {e}")
            self.finish_process_history(process_id, "ERROR", 0, 0)
            return False
            
        finally:
            self.jvlink.close()
    
    def update_data(self, from_date: str = None, data_spec: str = "DIFF") -> bool:
        """
        差分データ更新
        
        Args:
            from_date: 開始日（YYYYMMDDまたはNone）
            data_spec: データ種別
            
        Returns:
            成功時True
        """
        logger.info(f"データ更新開始: {data_spec}")
        
        # 最終更新日時を決定
        if from_date is None:
            from_time = self.get_last_update_time()
        else:
            from_time = from_date + "000000"
        
        logger.info(f"更新開始日時: {from_time}")
        
        # 処理履歴記録開始
        process_id = self.start_process_history("UPDATE", data_spec, from_time)
        
        try:
            # JV-Link初期化
            if not self.initialize_jvlink():
                return False
            
            # データ取得
            ret, read_count, download_count, last_timestamp = self.jvlink.open(
                data_spec=data_spec,
                from_time=from_time,
                option=1
            )
            
            if ret < 0:
                logger.error(f"JVOpenエラー: {self.jvlink.get_error_message(ret)}")
                self.finish_process_history(process_id, "ERROR", 0, 0)
                return False
            
            logger.info(f"更新対象: {read_count}件")
            
            # データ処理
            processed, errors = self.process_data(max_records=read_count)
            
            # 処理履歴更新
            self.finish_process_history(process_id, "SUCCESS", processed, errors)
            
            logger.info(f"更新完了: 処理{processed}件, エラー{errors}件")
            return True
            
        except Exception as e:
            logger.error(f"更新エラー: {e}")
            self.finish_process_history(process_id, "ERROR", 0, 0)
            return False
            
        finally:
            self.jvlink.close()
    
    def get_realtime_data(self, data_spec: str, race_key: str = "") -> bool:
        """
        リアルタイムデータ取得
        
        Args:
            data_spec: データ種別（REALTIME_SPEC参照）
            race_key: レースキー（空文字で当日全レース）
            
        Returns:
            成功時True
        """
        logger.info(f"リアルタイムデータ取得: {data_spec}")
        
        # 処理履歴記録開始
        process_id = self.start_process_history("REALTIME", data_spec, race_key)
        
        try:
            # JV-Link初期化
            if not self.initialize_jvlink():
                return False
            
            # リアルタイムデータ取得
            ret = self.jvlink.open_realtime(data_spec, race_key)
            
            if ret != 0:
                logger.error(f"JVRTOpenエラー: {self.jvlink.get_error_message(ret)}")
                self.finish_process_history(process_id, "ERROR", 0, 0)
                return False
            
            # データ処理
            processed, errors = self.process_data(max_records=10000)
            
            # 処理履歴更新
            self.finish_process_history(process_id, "SUCCESS", processed, errors)
            
            logger.info(f"リアルタイム取得完了: 処理{processed}件")
            return True
            
        except Exception as e:
            logger.error(f"リアルタイムエラー: {e}")
            self.finish_process_history(process_id, "ERROR", 0, 0)
            return False
            
        finally:
            self.jvlink.close()
    
    def process_data(self, max_records: int = 10000, batch_size: int = 100) -> tuple:
        """
        データ読み込みと処理（バッチ処理対応）
        
        Args:
            max_records: 最大処理レコード数
            batch_size: バッチサイズ（パフォーマンス向上）
            
        Returns:
            (処理件数, エラー件数)のタプル
        """
        processed = 0
        errors = 0
        file_count = 0
        last_filename = ""
        download_wait_count = 0
        batch_records = []  # バッチ処理用のレコード配列
        
        while processed < max_records:
            # データ読み込み
            ret, data, filename = self.jvlink.gets()
            
            if ret > 0:
                # 正常読み込み
                try:
                    # レコード解析
                    record = RecordParser.parse(data)
                    
                    if record:
                        batch_records.append(record)
                        processed += 1
                        
                        # バッチサイズに達したらまとめて保存
                        if len(batch_records) >= batch_size:
                            self._save_batch_records(batch_records)
                            batch_records = []
                        
                        # 進捗表示
                        if processed % 100 == 0:
                            logger.info(f"処理済: {processed}/{max_records}")
                            
                except Exception as e:
                    logger.error(f"レコード処理エラー: {e}")
                    errors += 1
                    
            elif ret == 0:
                # 全データ読み込み完了
                logger.info("全データ読み込み完了")
                break
                
            elif ret == -1:
                # ファイル切り替わり
                if filename != last_filename:
                    file_count += 1
                    last_filename = filename
                    logger.info(f"ファイル処理中: {filename} ({file_count})")
                    
            elif ret == -3:
                # ダウンロード中
                download_wait_count += 1
                if download_wait_count % 10 == 0:
                    status = self.jvlink.status()
                    logger.info(f"ダウンロード待機中... ({status}ファイル完了)")
                time.sleep(1)
                
            else:
                # エラー
                logger.error(f"JVReadエラー: {self.jvlink.get_error_message(ret)}")
                errors += 1
                if errors > 10:
                    logger.error("エラーが多いため処理を中断")
                    break
        
        # 残りのレコードを処理
        if batch_records:
            self._save_batch_records(batch_records)
        
        return (processed, errors)
    
    def _save_batch_records(self, records: List[Dict[str, Any]]) -> None:
        """
        レコードをバッチでデータベースに保存（パフォーマンス向上）
        
        Args:
            records: 保存対象のレコード配列
        """
        if not records:
            return
            
        try:
            with self.get_db_connection() as conn:
                # トランザクション開始
                conn.execute('BEGIN')
                
                try:
                    for record in records:
                        self.save_record(record, conn)
                    
                    # バッチ全体をコミット
                    conn.commit()
                    
                except Exception as e:
                    # エラー時はロールバック
                    conn.rollback()
                    logger.error(f"バッチ保存エラー: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"バッチ処理中にエラーが発生: {e}")
            # 個別保存にフォールバック
            self._save_records_individually(records)
    
    def _save_records_individually(self, records: List[Dict[str, Any]]) -> None:
        """
        レコードを個別に保存（フォールバック処理）
        
        Args:
            records: 保存対象のレコード配列
        """
        logger.info("個別保存モードにフォールバック")
        
        for record in records:
            try:
                with self.get_db_connection() as conn:
                    self.save_record(record, conn)
                    conn.commit()
            except Exception as e:
                logger.error(f"個別保存エラー: {e}")
    
    def save_record(self, record: Dict[str, Any], conn: sqlite3.Connection):
        """
        レコードをデータベースに保存
        
        Args:
            record: 解析済みレコード
            conn: データベース接続
        """
        cursor = conn.cursor()
        record_type = record.get('record_type')
        
        try:
            if record_type == 'RA':
                self.save_race_record(cursor, record)
            elif record_type == 'SE':
                self.save_result_record(cursor, record)
            elif record_type == 'UM':
                self.save_horse_record(cursor, record)
            elif record_type == 'O1':
                self.save_odds_record(cursor, record)
            elif record_type == 'WF':
                self.save_weight_record(cursor, record)
            elif record_type == 'YS':
                self.save_schedule_record(cursor, record)
            # 他のレコード種別も必要に応じて追加
            
        except Exception as e:
            logger.error(f"レコード保存エラー ({record_type}): {e}")
            raise
    
    def save_race_record(self, cursor: sqlite3.Cursor, record: Dict[str, Any]) -> None:
        """RAレコード保存"""
        race_key = self.build_race_key(record['race_key'])
        
        cursor.execute("""
            INSERT OR REPLACE INTO races (
                race_key, year, monthday, jyo_code, jyo_name,
                kaiji, nichiji, race_num, race_name, fukusho_name,
                grade_cd, syubetsu_cd, kyori, track_cd, track_name,
                tenko_cd, tenko, shiba_baba_cd, shiba_baba,
                dirt_baba_cd, dirt_baba, hassotime,
                toroku_tosu, syusso_tosu, data_kubun,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            race_key,
            record['race_key']['year'],
            record['race_key']['monthday'],
            record['race_key']['jyo_code'],
            CodeMaster.get_name('JYO', record['race_key']['jyo_code']),
            int(record['race_key']['kaiji']) if record['race_key']['kaiji'] else None,
            int(record['race_key']['nichiji']) if record['race_key']['nichiji'] else None,
            int(record['race_key']['race_num']) if record['race_key']['race_num'] else None,
            record['race_info']['race_name'],
            record['race_info']['fukusho_name'],
            record['race_info']['grade_cd'],
            record['race_info']['syubetsu_cd'],
            record['race_info']['kyori'],
            record['race_info']['track_cd'],
            CodeMaster.get_name('TRACK', record['race_info']['track_cd']),
            record['condition']['tenko_cd'],
            CodeMaster.get_name('TENKO', record['condition']['tenko_cd']),
            record['condition']['shiba_baba_cd'],
            CodeMaster.get_name('SHIBA_BABA', record['condition']['shiba_baba_cd']),
            record['condition']['dirt_baba_cd'],
            CodeMaster.get_name('DIRT_BABA', record['condition']['dirt_baba_cd']),
            record['hassotime'],
            record['toroku_tosu'],
            record['syusso_tosu'],
            record['data_kubun']
        ))
    
    def save_result_record(self, cursor: sqlite3.Cursor, record: Dict[str, Any]) -> None:
        """SEレコード保存"""
        race_key = self.build_race_key(record['race_key'])
        
        cursor.execute("""
            INSERT OR REPLACE INTO results (
                race_key, umaban, ketto_num, bamei,
                seibetsu_cd, barei, keiro_cd,
                jockey_code, jockey_name, jockey_name_ryaku,
                trainer_code, trainer_name, trainer_syozoku,
                futan, bataijyu, zogen,
                kakutei_jyuni, time, chakusa,
                tansho_odds, ninsiki,
                honsyo, fukasyo, data_kubun,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            race_key,
            record['umaban'],
            record['ketto_num'],
            record['bamei'],
            record['horse_info']['seibetsu_cd'],
            record['horse_info']['barei'],
            record['horse_info']['keiro_cd'],
            record['jockey']['code'],
            record['jockey']['name'],
            record['jockey']['name_ryaku'],
            record['trainer']['code'],
            record['trainer']['name'],
            record['trainer']['syozoku'],
            record['futan'],
            record['bataijyu'],
            record['zogen'],
            record['result']['kakutei_jyuni'],
            record['result']['time'],
            record['result']['chakusa'],
            record['result']['tansho_odds'],
            record['result']['ninsiki'],
            record['prize']['honsyo'],
            record['prize']['fukasyo'],
            record['data_kubun']
        ))
    
    def save_horse_record(self, cursor: sqlite3.Cursor, record: Dict[str, Any]) -> None:
        """UMレコード保存"""
        cursor.execute("""
            INSERT OR REPLACE INTO horses (
                ketto_num, bamei, birth_date,
                seibetsu_cd, hinsyu_cd, keiro_cd,
                keito, father, mother, bms,
                tozai_cd, trainer_code, trainer_name,
                banushi_code, banushi_name,
                breeder_code, breeder_name, sanchi_name,
                del_kubun, data_kubun,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            record['ketto_num'],
            record['bamei'],
            record['birth_date']['formatted'],
            record['horse_info']['seibetsu_cd'],
            record['horse_info']['hinsyu_cd'],
            record['horse_info']['keiro_cd'],
            record['keito'],
            record['blood']['father'],
            record['blood']['mother'],
            record['blood']['bms'],
            record['tozai_cd'],
            record['trainer']['code'],
            record['trainer']['name'],
            record['banushi']['code'],
            record['banushi']['name'],
            record['breeder']['code'],
            record['breeder']['name'],
            record['sanchi_name'],
            record['del_kubun'],
            record['data_kubun']
        ))
    
    def save_odds_record(self, cursor: sqlite3.Cursor, record: Dict[str, Any]) -> None:
        """O1レコード（オッズ）保存"""
        race_key = self.build_race_key(record['race_key'])
        
        for odds in record.get('odds', []):
            cursor.execute("""
                INSERT OR REPLACE INTO odds (
                    race_key, umaban,
                    tansho_odds, fukusho_odds_low, fukusho_odds_high,
                    tansho_ninki, fukusho_ninki,
                    data_kubun
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                race_key,
                odds['umaban'],
                odds['tansho_odds'],
                odds['fukusho_odds_low'],
                odds['fukusho_odds_high'],
                odds['tansho_ninki'],
                odds['fukusho_ninki'],
                record['data_kubun']
            ))
    
    def save_weight_record(self, cursor: sqlite3.Cursor, record: Dict[str, Any]) -> None:
        """WFレコード（馬体重）保存"""
        race_key = self.build_race_key(record['race_key'])
        
        for weight in record.get('weights', []):
            cursor.execute("""
                INSERT OR REPLACE INTO weights (
                    race_key, umaban,
                    bataijyu, zogen_fuka, zogen,
                    data_kubun
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                race_key,
                weight['umaban'],
                weight['bataijyu'],
                weight['zogen_fuka'],
                weight['zogen'],
                record['data_kubun']
            ))
    
    def save_schedule_record(self, cursor: sqlite3.Cursor, record: Dict[str, Any]) -> None:
        """YSレコード（年間スケジュール）保存"""
        for kaisai in record.get('kaisai_info', []):
            cursor.execute("""
                INSERT OR REPLACE INTO schedules (
                    year, kaiji_date, jyo_code, jyo_name,
                    kaiji, nichiji, youbi, henko_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['year'],
                kaisai['kaiji_date'],
                kaisai['jyo_code'],
                CodeMaster.get_name('JYO', kaisai['jyo_code']),
                int(kaisai['kaiji']) if kaisai['kaiji'] else None,
                int(kaisai['nichiji']) if kaisai['nichiji'] else None,
                kaisai['youbi'],
                record['henko_id']
            ))
    
    def build_race_key(self, race_key_dict: Dict[str, str]) -> str:
        """レースキー構築"""
        year = race_key_dict['year']
        monthday = race_key_dict['monthday']
        jyo = race_key_dict['jyo_code']
        kaiji = race_key_dict['kaiji']
        nichiji = race_key_dict['nichiji']
        race = race_key_dict['race_num']
        return f"{year}{monthday}{jyo}{kaiji}{nichiji}{race}"
    
    def get_last_update_time(self) -> str:
        """最終更新日時取得"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
        
        # 処理履歴から最終成功日時を取得
        cursor.execute("""
            SELECT to_time 
            FROM process_history 
            WHERE status = 'SUCCESS' 
            ORDER BY finished_at DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        
            # なければレーステーブルから取得
            cursor.execute("""
                SELECT MAX(year || monthday || '000000') 
                FROM races
            """)
            
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            
            # デフォルトは1年前
            one_year_ago = datetime.now() - timedelta(days=365)
            return one_year_ago.strftime("%Y%m%d000000")
    
    def start_process_history(self, process_type: str, data_spec: str, from_time: str) -> int:
        """処理履歴開始記録"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO process_history (
                    process_type, data_spec, from_time, 
                    status, started_at
                ) VALUES (?, ?, ?, 'RUNNING', CURRENT_TIMESTAMP)
            """, (process_type, data_spec, from_time))
            conn.commit()
            return cursor.lastrowid
    
    def finish_process_history(self, process_id: int, status: str, 
                              processed: int, errors: int) -> None:
        """処理履歴終了記録"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE process_history 
                SET status = ?, 
                    processed_count = ?, 
                    error_count = ?,
                    to_time = CURRENT_TIMESTAMP,
                    finished_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, processed, errors, process_id))
            conn.commit()
    
    def close(self):
        """終了処理"""
        # 旧式のコネクションがあれば閉じる
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
            except sqlite3.Error as e:
                logger.warning(f"データベース接続終了時エラー: {e}")
            finally:
                self.conn = None
        
        # JV-Link終了
        if self.jvlink:
            try:
                self.jvlink.close()
            except Exception as e:
                logger.warning(f"JV-Link終了時エラー: {e}")
    
    def __del__(self):
        """デストラクタ"""
        self.close()


def test_manager():
    """マネージャーのテスト（コンテキストマネージャー使用）"""
    print("JV-Data Managerテスト")
    print("=" * 50)
    
    # コンテキストマネージャーを使用して自動的にリソースクリーンアップ
    with JVDataManager("test.db", "test_data") as manager:
        # 年間スケジュール取得（軽量データ）
        success = manager.download_setup_data("YSCH")
        
        if success:
            print("テスト成功")
        else:
            print("テスト失敗")
    # ここで自動的にmanager.close()が呼ばれる
    
    print("=" * 50)
    print("テスト完了")


if __name__ == "__main__":
    test_manager()