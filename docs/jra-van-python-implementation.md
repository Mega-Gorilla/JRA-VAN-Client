# JRA-VAN DataLab Python実装詳細ガイド

## 概要
JRA-VAN DataLab SDK Ver4.9.0.2を基にしたPython実装の詳細ガイドです。

## 環境構築

### 必要条件
- Windows OS（JV-LinkはWindows専用）
- Python 32bit版（推奨）または64bit版（DLLサロゲート設定必要）
- pywin32パッケージ
- JRA-VAN DataLab契約（月額2,090円）

### インストール手順

#### 1. JV-Linkの登録
```bash
# SDKに含まれるJV-Link.exeを実行して登録
cd "JRA-VAN Data Lab. SDK Ver4.9.0.2\JV-Link"
JV-Link.exe /regserver
```

#### 2. Python環境セットアップ
```bash
# 32bit版Python使用時
pip install pywin32

# 文字コード処理用
pip install chardet
```

## Python実装コード

### 基本実装クラス

```python
"""
JRA-VAN DataLab Python実装
Based on JRA-VAN SDK Ver4.9.0.2
"""

import win32com.client
import time
import os
import struct
from datetime import datetime
import sqlite3
from typing import List, Dict, Optional, Tuple

class JVDataParser:
    """JV-Dataパーサークラス"""
    
    @staticmethod
    def mid_b2s(data: bytes, start: int, length: int) -> str:
        """
        バイト配列から文字列を切り出し（SDK仕様準拠）
        Args:
            data: バイト配列
            start: 開始位置（1から始まる）
            length: バイト長
        Returns:
            切り出した文字列
        """
        # SDK仕様では位置は1から始まるが、Pythonは0から
        actual_start = start - 1
        try:
            return data[actual_start:actual_start + length].decode('shift-jis').strip()
        except:
            return data[actual_start:actual_start + length].decode('shift-jis', errors='ignore').strip()
    
    @staticmethod
    def parse_ymd(data: bytes, start: int) -> dict:
        """年月日パース（YMD構造体）"""
        return {
            'year': JVDataParser.mid_b2s(data, start, 4),
            'month': JVDataParser.mid_b2s(data, start + 4, 2),
            'day': JVDataParser.mid_b2s(data, start + 6, 2)
        }
    
    @staticmethod
    def parse_hms(data: bytes, start: int) -> dict:
        """時分秒パース（HMS構造体）"""
        return {
            'hour': JVDataParser.mid_b2s(data, start, 2),
            'minute': JVDataParser.mid_b2s(data, start + 2, 2),
            'second': JVDataParser.mid_b2s(data, start + 4, 2)
        }

class JVLinkWrapper:
    """JV-Link COMオブジェクトのラッパークラス"""
    
    # JV-Link CLSID
    CLSID_JVLINK = "{02AB1774-0C41-11D7-916F-0003479BEB3F}"
    
    # データ種別定数
    DATA_SPEC = {
        'RACE': 'RACE',      # レース情報
        'DIFF': 'DIFF',      # 差分データ
        'BLOD': 'BLOD',      # 血統データ
        'MING': 'MING',      # マイニングデータ
        'SNAP': 'SNAP',      # スナップショット
        'YSCH': 'YSCH',      # 年間スケジュール
    }
    
    # 速報データ種別
    REALTIME_SPEC = {
        'ODDS_WIN_PLACE': '0B12',  # 単複枠オッズ
        'ODDS_QUINELLA': '0B13',   # 馬連オッズ
        'ODDS_WIDE': '0B14',        # ワイドオッズ
        'WEIGHT': '0B15',           # 馬体重
        'ODDS_EXACTA': '0B16',      # 馬単オッズ
        'ODDS_TRIO': '0B17',        # 3連複オッズ
        'ODDS_TRIFECTA': '0B18',    # 3連単オッズ
        'RESULT': '0B20',           # 速報成績
        'VOTE': '0B30',             # 票数
    }
    
    # エラーコード
    ERROR_CODES = {
        0: "正常終了",
        -1: "パラメータエラー/ファイル切り替わり",
        -2: "初期化前エラー",
        -3: "ファイルダウンロード中",
        -100: "その他エラー",
        -201: "JVInit未実行",
        -202: "前回のJVOpenが開いたまま",
        -203: "パラメータエラー",
        -211: "サービスキー認証エラー",
        -403: "サーバーメンテナンス中",
        -502: "サーバーエラー",
        -503: "読み込みタイムアウト",
    }
    
    def __init__(self):
        """コンストラクタ"""
        self.jvlink = None
        self.is_initialized = False
        self.is_open = False
        
    def initialize(self, sid: str = "UNKNOWN") -> int:
        """
        JV-Link初期化
        Args:
            sid: ソフトウェアID
        Returns:
            0: 正常終了、その他: エラーコード
        """
        try:
            # COMオブジェクト作成
            self.jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
            
            # JVInit実行
            ret = self.jvlink.JVInit(sid)
            
            if ret == 0:
                self.is_initialized = True
                print(f"JV-Link初期化成功 (Version: {self.get_version()})")
            else:
                print(f"JV-Link初期化エラー: {self.get_error_message(ret)}")
                
            return ret
            
        except Exception as e:
            print(f"JV-Link初期化例外: {e}")
            return -100
    
    def get_version(self) -> str:
        """JV-Linkバージョン取得"""
        if self.jvlink:
            try:
                return self.jvlink.m_JVLinkVersion
            except:
                return "Unknown"
        return ""
    
    def get_error_message(self, code: int) -> str:
        """エラーコードからメッセージ取得"""
        return self.ERROR_CODES.get(code, f"未定義エラー({code})")
    
    def open(self, data_spec: str, from_time: str = "99999999999999", 
             option: int = 1) -> Tuple[int, int, int, str]:
        """
        蓄積系データオープン
        Args:
            data_spec: データ種別
            from_time: 取得開始日時（YYYYMMDDHHMMSSまたは99999999999999）
            option: 1:通常 2:今週データ 3:セットアップデータ
        Returns:
            (戻り値, 読込対象数, DL数, 最終ファイルタイムスタンプ)
        """
        if not self.is_initialized:
            return (-201, 0, 0, "")
        
        if self.is_open:
            self.close()
        
        # pywin32では出力パラメータはタプルで返される
        result = self.jvlink.JVOpen(data_spec, from_time, option, 0, 0, "")
        
        if isinstance(result, tuple) and len(result) == 4:
            ret_code, read_count, download_count, last_timestamp = result
        else:
            ret_code = result
            read_count = download_count = 0
            last_timestamp = ""
        
        if ret_code >= 0:
            self.is_open = True
            
        return (ret_code, read_count, download_count, last_timestamp)
    
    def open_realtime(self, data_spec: str, key: str = "") -> int:
        """
        速報系データオープン
        Args:
            data_spec: データ種別（REALTIME_SPEC参照）
            key: レースキー（空文字で当日全レース）
        Returns:
            戻り値コード
        """
        if not self.is_initialized:
            return -201
        
        if self.is_open:
            self.close()
        
        ret = self.jvlink.JVRTOpen(data_spec, key)
        
        if ret == 0:
            self.is_open = True
            
        return ret
    
    def read(self, buffer_size: int = 110000) -> Tuple[int, bytes, str]:
        """
        データ読み込み
        Args:
            buffer_size: バッファサイズ
        Returns:
            (戻り値, データ, ファイル名)
        """
        if not self.is_open:
            return (-201, b"", "")
        
        # JVReadを呼び出し
        result = self.jvlink.JVRead(buffer_size, "")
        
        if isinstance(result, tuple) and len(result) == 3:
            ret_code, data, filename = result
        else:
            return (-100, b"", "")
        
        # 文字列をバイト列に変換
        if isinstance(data, str):
            data = data.encode('shift-jis', errors='ignore')
        
        return (ret_code, data, filename)
    
    def status(self) -> int:
        """
        ダウンロード進捗取得
        Returns:
            ダウンロード済みファイル数
        """
        if self.jvlink:
            return self.jvlink.JVStatus()
        return -1
    
    def cancel(self):
        """ダウンロードキャンセル"""
        if self.jvlink:
            self.jvlink.JVCancel()
    
    def close(self) -> int:
        """
        JV-Link終了処理
        Returns:
            戻り値コード
        """
        if self.jvlink and self.is_open:
            ret = self.jvlink.JVClose()
            self.is_open = False
            return ret
        return 0
    
    def set_save_path(self, path: str) -> int:
        """
        保存パス設定
        Args:
            path: 保存先パス
        Returns:
            戻り値コード
        """
        if self.jvlink:
            return self.jvlink.JVSetSavePath(path)
        return -1
    
    def set_save_flag(self, flag: int) -> int:
        """
        保存フラグ設定
        Args:
            flag: 0:保存しない 1:保存する
        Returns:
            戻り値コード
        """
        if self.jvlink:
            return self.jvlink.JVSetSaveFlag(flag)
        return -1
    
    def set_ui_properties(self) -> int:
        """JVLink設定ダイアログ表示"""
        if self.jvlink:
            return self.jvlink.JVSetUIProperties()
        return -1
    
    def __del__(self):
        """デストラクタ"""
        if self.is_open:
            self.close()

class JVDataRecord:
    """レコード種別と解析クラス"""
    
    RECORD_TYPES = {
        'RA': 'レース詳細',
        'SE': '馬毎レース情報',
        'HR': '払戻',
        'H1': '単勝オッズ',
        'H6': '3連単オッズ',
        'O1': '単複オッズ',
        'O2': '馬連オッズ',
        'O3': 'ワイドオッズ',
        'O4': '馬単オッズ',
        'O5': '3連複オッズ',
        'O6': '3連単オッズ',
        'UM': '競走馬マスタ',
        'KS': '騎手マスタ',
        'CH': '調教師マスタ',
        'BR': '生産者マスタ',
        'BN': '馬主マスタ',
        'RC': 'レコードマスタ',
        'HC': '繁殖牝馬マスタ',
        'HS': '種牡馬マスタ',
        'YS': '年間スケジュール',
        'BT': '血統',
        'CS': 'コース別成績',
        'DM': '競争別成績',
        'TM': 'タイム型データマイニング',
        'WF': '馬体重',
        'JG': '重賞勝馬',
    }
    
    @classmethod
    def parse_record(cls, data: bytes) -> dict:
        """
        レコード解析
        Args:
            data: レコードデータ
        Returns:
            解析結果辞書
        """
        if len(data) < 2:
            return None
        
        record_type = data[0:2].decode('ascii', errors='ignore')
        
        if record_type == 'RA':
            return cls.parse_race_record(data)
        elif record_type == 'SE':
            return cls.parse_horse_race_record(data)
        elif record_type == 'UM':
            return cls.parse_horse_master_record(data)
        # 他のレコード種別も同様に実装
        
        return {
            'record_type': record_type,
            'description': cls.RECORD_TYPES.get(record_type, '不明'),
            'raw_data': data
        }
    
    @classmethod
    def parse_race_record(cls, data: bytes) -> dict:
        """RAレコード（レース詳細）解析"""
        parser = JVDataParser()
        
        record = {
            'record_type': parser.mid_b2s(data, 1, 2),
            'data_kubun': parser.mid_b2s(data, 3, 1),
            'make_date': parser.parse_ymd(data, 4),
            'make_time': parser.parse_hms(data, 11),
            'race_key': {
                'kaiji_date': parser.parse_ymd(data, 17),
                'jyo_code': parser.mid_b2s(data, 25, 2),
                'kaiji': parser.mid_b2s(data, 27, 2),
                'nichiji': parser.mid_b2s(data, 29, 2),
                'race_num': parser.mid_b2s(data, 31, 2),
            },
            'race_info': {
                'youbi': parser.mid_b2s(data, 33, 2),
                'race_name': parser.mid_b2s(data, 35, 60),
                'fukusho_name': parser.mid_b2s(data, 95, 60),
                'kakutei_jyuni': parser.mid_b2s(data, 155, 100),
                'grade': parser.mid_b2s(data, 255, 1),
                'gradecd': parser.mid_b2s(data, 256, 1),
                'syubetsucd': parser.mid_b2s(data, 257, 2),
                'kigo_cd': parser.mid_b2s(data, 259, 3),
                'jyuryo_cd': parser.mid_b2s(data, 262, 1),
                'jyoken': parser.mid_b2s(data, 263, 2),
                'kyori': parser.mid_b2s(data, 265, 4),
                'track_cd': parser.mid_b2s(data, 269, 2),
                'course_kbn': parser.mid_b2s(data, 271, 1),
            },
            'hassotime': parser.mid_b2s(data, 272, 4),
            'toroku_tosu': parser.mid_b2s(data, 276, 2),
            'syusso_tosu': parser.mid_b2s(data, 278, 2),
            'nyusen_tosu': parser.mid_b2s(data, 280, 2),
            'tenko_baba': {
                'tenko_cd': parser.mid_b2s(data, 282, 1),
                'shiba_baba_cd': parser.mid_b2s(data, 283, 1),
                'dirt_baba_cd': parser.mid_b2s(data, 284, 1),
            },
            'lap_time': [parser.mid_b2s(data, 285 + i*3, 3) for i in range(25)],
            'syogai_mile_time': parser.mid_b2s(data, 360, 4),
            'haron_time_s': [parser.mid_b2s(data, 364 + i*3, 3) for i in range(4)],
            'haron_time_l': [parser.mid_b2s(data, 376 + i*3, 3) for i in range(3)],
        }
        
        return record
    
    @classmethod
    def parse_horse_race_record(cls, data: bytes) -> dict:
        """SEレコード（馬毎レース情報）解析"""
        parser = JVDataParser()
        
        record = {
            'record_type': parser.mid_b2s(data, 1, 2),
            'data_kubun': parser.mid_b2s(data, 3, 1),
            'make_date': parser.parse_ymd(data, 4),
            'race_key': {
                'kaiji_date': parser.parse_ymd(data, 11),
                'jyo_code': parser.mid_b2s(data, 19, 2),
                'kaiji': parser.mid_b2s(data, 21, 2),
                'nichiji': parser.mid_b2s(data, 23, 2),
                'race_num': parser.mid_b2s(data, 25, 2),
            },
            'umaban': parser.mid_b2s(data, 27, 2),
            'ketto_num': parser.mid_b2s(data, 29, 10),
            'bamei': parser.mid_b2s(data, 39, 36),
            'seibetsucd': parser.mid_b2s(data, 75, 1),
            'barei': parser.mid_b2s(data, 76, 2),
            'tozu_cd': parser.mid_b2s(data, 78, 1),
            'hinsyucd': parser.mid_b2s(data, 79, 1),
            'keiro_cd': parser.mid_b2s(data, 80, 2),
            'owner': {
                'code': parser.mid_b2s(data, 82, 6),
                'name': parser.mid_b2s(data, 88, 64),
            },
            'futan': parser.mid_b2s(data, 152, 3),
            'blinker': parser.mid_b2s(data, 155, 1),
            'jockey': {
                'code': parser.mid_b2s(data, 156, 5),
                'name': parser.mid_b2s(data, 161, 34),
                'name_ryakusho': parser.mid_b2s(data, 195, 8),
            },
            'bataijyu': parser.mid_b2s(data, 203, 3),
            'zogen': parser.mid_b2s(data, 206, 3),
            'ijyo': parser.mid_b2s(data, 209, 1),
            'trainer': {
                'code': parser.mid_b2s(data, 210, 5),
                'name': parser.mid_b2s(data, 215, 34),
                'name_ryakusho': parser.mid_b2s(data, 249, 8),
            },
            'banusi': {
                'code': parser.mid_b2s(data, 257, 6),
                'name': parser.mid_b2s(data, 263, 64),
            },
            'prize': {
                'honsyo': parser.mid_b2s(data, 327, 8),
                'fukasyo': parser.mid_b2s(data, 335, 8),
                'shutokujyo': parser.mid_b2s(data, 343, 8),
                'shutoku': parser.mid_b2s(data, 351, 8),
            },
        }
        
        return record
    
    @classmethod  
    def parse_horse_master_record(cls, data: bytes) -> dict:
        """UMレコード（競走馬マスタ）解析"""
        parser = JVDataParser()
        
        record = {
            'record_type': parser.mid_b2s(data, 1, 2),
            'data_kubun': parser.mid_b2s(data, 3, 1),
            'make_date': parser.parse_ymd(data, 4),
            'ketto_num': parser.mid_b2s(data, 11, 10),
            'del_kubun': parser.mid_b2s(data, 21, 1),
            'touroku_date': parser.parse_ymd(data, 22),
            'massyo_date': parser.parse_ymd(data, 30),
            'bamei': parser.mid_b2s(data, 38, 36),
            'birth_date': parser.parse_ymd(data, 74),
            'seibetsucd': parser.mid_b2s(data, 82, 1),
            'hinsyucd': parser.mid_b2s(data, 83, 1),
            'keiro_cd': parser.mid_b2s(data, 84, 2),
            'keito': parser.mid_b2s(data, 86, 60),
            'blood': {
                'father': parser.mid_b2s(data, 146, 10),
                'mother': parser.mid_b2s(data, 156, 10),
                'bms': parser.mid_b2s(data, 166, 10),
            },
        }
        
        return record

class JVDataManager:
    """JV-Dataの取得と保存を管理するクラス"""
    
    def __init__(self, db_path: str = "jravan.db"):
        """
        初期化
        Args:
            db_path: SQLiteデータベースパス
        """
        self.jvlink = JVLinkWrapper()
        self.db_path = db_path
        self.conn = None
        self.setup_database()
        
    def setup_database(self):
        """データベース初期設定"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # レーステーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS races (
                race_key TEXT PRIMARY KEY,
                race_date TEXT,
                jyo_code TEXT,
                race_num INTEGER,
                race_name TEXT,
                grade TEXT,
                distance INTEGER,
                track_cd TEXT,
                syusso_tosu INTEGER,
                raw_data BLOB,
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
                jockey_code TEXT,
                jockey_name TEXT,
                trainer_code TEXT,
                trainer_name TEXT,
                kakutei_jyuni INTEGER,
                time TEXT,
                odds REAL,
                popular INTEGER,
                raw_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(race_key) REFERENCES races(race_key)
            )
        """)
        
        # 競走馬マスタテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS horses (
                ketto_num TEXT PRIMARY KEY,
                bamei TEXT,
                birth_date TEXT,
                seibetsucd TEXT,
                keiro_cd TEXT,
                father TEXT,
                mother TEXT,
                bms TEXT,
                raw_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # インデックス作成
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_race_date ON races(race_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ketto_num ON results(ketto_num)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jockey ON results(jockey_code)")
        
        self.conn.commit()
    
    def download_setup_data(self):
        """セットアップデータ取得（初回実行時）"""
        print("セットアップデータ取得開始...")
        
        # JV-Link初期化
        ret = self.jvlink.initialize()
        if ret != 0:
            return False
        
        # セットアップデータ取得（オプション=3）
        ret, read_count, download_count, last_timestamp = self.jvlink.open(
            data_spec="RACE",
            from_time="99999999999999",
            option=3  # セットアップデータ
        )
        
        if ret < 0:
            print(f"JVOpenエラー: {self.jvlink.get_error_message(ret)}")
            return False
        
        print(f"読込対象: {read_count}件, ダウンロード: {download_count}ファイル")
        
        # データ読み込みと保存
        self.process_data(max_records=read_count)
        
        self.jvlink.close()
        return True
    
    def update_data(self, from_date: str = None):
        """
        差分データ更新
        Args:
            from_date: 開始日（YYYYMMDDまたはNone）
        """
        print("データ更新開始...")
        
        # JV-Link初期化
        ret = self.jvlink.initialize()
        if ret != 0:
            return False
        
        # 最終更新日時を取得
        if from_date is None:
            cursor = self.conn.cursor()
            cursor.execute("SELECT MAX(updated_at) FROM races")
            last_update = cursor.fetchone()[0]
            if last_update:
                from_time = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")
                from_time = from_time.strftime("%Y%m%d%H%M%S")
            else:
                from_time = "99999999999999"
        else:
            from_time = from_date + "000000"
        
        # 差分データ取得
        ret, read_count, download_count, last_timestamp = self.jvlink.open(
            data_spec="DIFF",
            from_time=from_time,
            option=1
        )
        
        if ret < 0:
            print(f"JVOpenエラー: {self.jvlink.get_error_message(ret)}")
            return False
        
        print(f"更新対象: {read_count}件")
        
        # データ処理
        self.process_data(max_records=read_count)
        
        self.jvlink.close()
        return True
    
    def process_data(self, max_records: int = 1000):
        """
        データ読み込みと処理
        Args:
            max_records: 最大処理レコード数
        """
        processed = 0
        errors = 0
        file_count = 0
        last_filename = ""
        
        while processed < max_records:
            # データ読み込み
            ret, data, filename = self.jvlink.read()
            
            if ret > 0:
                # 正常読み込み
                try:
                    # レコード解析
                    record = JVDataRecord.parse_record(data)
                    
                    if record:
                        # データベース保存
                        self.save_record(record)
                        processed += 1
                        
                        # 進捗表示
                        if processed % 100 == 0:
                            print(f"処理済: {processed}/{max_records}")
                            
                except Exception as e:
                    print(f"レコード処理エラー: {e}")
                    errors += 1
                    
            elif ret == 0:
                # 全データ読み込み完了
                print("全データ読み込み完了")
                break
                
            elif ret == -1:
                # ファイル切り替わり
                if filename != last_filename:
                    file_count += 1
                    last_filename = filename
                    print(f"ファイル: {filename} ({file_count})")
                    
            elif ret == -3:
                # ダウンロード中
                status = self.jvlink.status()
                print(f"ダウンロード中... ({status}ファイル完了)")
                time.sleep(1)
                
            else:
                # エラー
                print(f"JVReadエラー: {self.jvlink.get_error_message(ret)}")
                errors += 1
                if errors > 10:
                    print("エラーが多いため処理を中断")
                    break
        
        # コミット
        self.conn.commit()
        
        print(f"処理完了: {processed}件 (エラー: {errors}件)")
    
    def save_record(self, record: dict):
        """
        レコードをデータベースに保存
        Args:
            record: 解析済みレコード
        """
        cursor = self.conn.cursor()
        record_type = record.get('record_type')
        
        if record_type == 'RA':
            # レースデータ保存
            race_key = self.build_race_key(record['race_key'])
            
            cursor.execute("""
                INSERT OR REPLACE INTO races (
                    race_key, race_date, jyo_code, race_num,
                    race_name, grade, distance, track_cd, 
                    syusso_tosu, raw_data, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                race_key,
                self.format_date(record['race_key']['kaiji_date']),
                record['race_key']['jyo_code'],
                int(record['race_key']['race_num']),
                record['race_info']['race_name'],
                record['race_info']['grade'],
                int(record['race_info']['kyori']),
                record['race_info']['track_cd'],
                int(record['syusso_tosu']),
                record.get('raw_data')
            ))
            
        elif record_type == 'SE':
            # 馬毎レース情報保存
            race_key = self.build_race_key(record['race_key'])
            
            cursor.execute("""
                INSERT OR REPLACE INTO results (
                    race_key, umaban, ketto_num, bamei,
                    jockey_code, jockey_name, trainer_code, trainer_name,
                    raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                race_key,
                int(record['umaban']),
                record['ketto_num'],
                record['bamei'],
                record['jockey']['code'],
                record['jockey']['name'],
                record['trainer']['code'],
                record['trainer']['name'],
                record.get('raw_data')
            ))
            
        elif record_type == 'UM':
            # 競走馬マスタ保存
            cursor.execute("""
                INSERT OR REPLACE INTO horses (
                    ketto_num, bamei, birth_date, seibetsucd,
                    keiro_cd, father, mother, bms,
                    raw_data, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                record['ketto_num'],
                record['bamei'],
                self.format_date(record['birth_date']),
                record['seibetsucd'],
                record['keiro_cd'],
                record['blood']['father'],
                record['blood']['mother'],
                record['blood']['bms'],
                record.get('raw_data')
            ))
    
    def build_race_key(self, race_key_dict: dict) -> str:
        """レースキー構築"""
        date = self.format_date(race_key_dict['kaiji_date'])
        jyo = race_key_dict['jyo_code']
        kaiji = race_key_dict['kaiji']
        nichiji = race_key_dict['nichiji']
        race = race_key_dict['race_num']
        return f"{date}{jyo}{kaiji}{nichiji}{race}"
    
    def format_date(self, date_dict: dict) -> str:
        """日付フォーマット"""
        if isinstance(date_dict, dict):
            return f"{date_dict['year']}{date_dict['month']}{date_dict['day']}"
        return date_dict
    
    def get_realtime_odds(self, race_date: str = None):
        """
        リアルタイムオッズ取得
        Args:
            race_date: レース日（YYYYMMDDまたはNone）
        """
        print("リアルタイムオッズ取得開始...")
        
        # JV-Link初期化
        ret = self.jvlink.initialize()
        if ret != 0:
            return False
        
        # 単複枠オッズ取得
        key = race_date if race_date else ""
        ret = self.jvlink.open_realtime(
            JVLinkWrapper.REALTIME_SPEC['ODDS_WIN_PLACE'],
            key
        )
        
        if ret != 0:
            print(f"JVRTOpenエラー: {self.jvlink.get_error_message(ret)}")
            return False
        
        # データ処理
        while True:
            ret, data, filename = self.jvlink.read()
            
            if ret > 0:
                # オッズデータ処理
                record = JVDataRecord.parse_record(data)
                print(f"オッズ更新: {record.get('record_type')}")
                
            elif ret == 0:
                print("オッズデータ取得完了")
                break
                
            else:
                time.sleep(1)
        
        self.jvlink.close()
        return True
    
    def close(self):
        """終了処理"""
        if self.conn:
            self.conn.close()
        if self.jvlink:
            self.jvlink.close()

# 使用例
if __name__ == "__main__":
    # データマネージャ初期化
    manager = JVDataManager("jravan.db")
    
    # 初回セットアップ（大量データ取得）
    # manager.download_setup_data()
    
    # 差分更新（日次実行）
    manager.update_data()
    
    # リアルタイムオッズ取得
    # manager.get_realtime_odds()
    
    # 終了処理
    manager.close()
    
    print("処理完了")
```

## 実行方法

### 1. 初回セットアップ
```python
from jvlink_client import JVDataManager

# データマネージャ初期化
manager = JVDataManager("jravan.db")

# セットアップデータ取得（初回のみ）
manager.download_setup_data()

manager.close()
```

### 2. 日次更新
```python
# 差分データ更新
manager = JVDataManager("jravan.db")
manager.update_data()  # 最終更新日時から自動取得
manager.close()
```

### 3. リアルタイムデータ取得
```python
# 当日のオッズ取得
manager = JVDataManager("jravan.db")
manager.get_realtime_odds()
manager.close()
```

## トラブルシューティング

### 32bit/64bit問題の解決

#### 方法1: 32bit Python使用
```bash
# 32bit版Pythonインストール
# Python公式サイトから「Windows installer (32-bit)」をダウンロード
```

#### 方法2: DLLサロゲート設定（64bit Python）
```python
import winreg

def setup_dll_surrogate():
    """64bit PythonでJV-Linkを使用するための設定"""
    
    # レジストリキー
    key_path = r"SOFTWARE\Classes\CLSID\{02AB1774-0C41-11D7-916F-0003479BEB3F}\InProcServer32"
    
    try:
        # レジストリ編集（管理者権限必要）
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, 
                            winreg.KEY_ALL_ACCESS)
        
        # DllSurrogateキー追加
        winreg.SetValueEx(key, "DllSurrogate", 0, winreg.REG_SZ, "")
        
        winreg.CloseKey(key)
        print("DLLサロゲート設定完了")
        
    except Exception as e:
        print(f"レジストリ設定エラー: {e}")
        print("管理者権限で実行してください")

# 設定実行
setup_dll_surrogate()
```

### 文字化け対策
```python
def decode_shift_jis(data: bytes) -> str:
    """Shift-JISデータのデコード"""
    try:
        return data.decode('shift-jis')
    except:
        # エラー時は無視してデコード
        return data.decode('shift-jis', errors='ignore')
```

### メモリ最適化
```python
def process_large_data_optimized(jvlink, batch_size=1000):
    """大量データの効率的処理"""
    batch = []
    
    while True:
        ret, data, filename = jvlink.read()
        
        if ret > 0:
            # バッチに追加
            batch.append(data)
            
            # バッチサイズに達したら処理
            if len(batch) >= batch_size:
                process_batch(batch)
                batch.clear()
                
        elif ret == 0:
            # 残りを処理
            if batch:
                process_batch(batch)
            break
```

## パフォーマンス最適化

### 並列処理による高速化
```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def parallel_record_processing(records):
    """並列レコード処理"""
    
    # CPU数に応じてワーカー数設定
    num_workers = multiprocessing.cpu_count()
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # レコードを並列処理
        futures = []
        for record in records:
            future = executor.submit(process_single_record, record)
            futures.append(future)
        
        # 結果収集
        results = []
        for future in futures:
            result = future.result()
            results.append(result)
    
    return results
```

### SQLiteパフォーマンスチューニング
```python
def optimize_sqlite_performance(conn):
    """SQLiteパフォーマンス最適化"""
    cursor = conn.cursor()
    
    # WALモード有効化
    cursor.execute("PRAGMA journal_mode = WAL")
    
    # キャッシュサイズ増加
    cursor.execute("PRAGMA cache_size = -64000")  # 64MB
    
    # 同期モード調整
    cursor.execute("PRAGMA synchronous = NORMAL")
    
    # メモリ最適化
    cursor.execute("PRAGMA temp_store = MEMORY")
    
    conn.commit()
```

## まとめ

JRA-VAN DataLabのPython実装により、以下が実現できます：

1. **公式競馬データの取得**
   - レース情報、馬情報、オッズ等
   - リアルタイムデータ対応

2. **効率的なデータ管理**
   - SQLiteによるローカルDB
   - 差分更新による効率化

3. **柔軟な拡張性**
   - 機械学習への適用
   - トランスフォーマーモデルとの連携

4. **本番運用対応**
   - エラーハンドリング
   - パフォーマンス最適化

月額2,090円で高品質な競馬データを活用した予測モデル開発が可能です。

---
*最終更新日: 2025年8月28日*
*Based on JRA-VAN SDK Ver4.9.0.2*