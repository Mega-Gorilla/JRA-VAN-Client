"""
JV-Data Parser Module
JV-Dataの固定長フォーマットをパースするモジュール

Based on JRA-VAN SDK Ver4.9.0.2
"""

from typing import Dict, Any, List, Optional
import struct
from datetime import datetime


class JVDataParser:
    """JV-Data固定長フォーマットパーサー"""
    
    @staticmethod
    def mid_b2s(data: bytes, start: int, length: int) -> str:
        """
        バイト配列から文字列を切り出し（SDK準拠）
        
        Args:
            data: バイト配列
            start: 開始位置（1から始まる）
            length: バイト長
            
        Returns:
            切り出した文字列（前後の空白削除）
        """
        # SDK仕様では位置は1から始まるが、Pythonは0から
        actual_start = start - 1
        try:
            result = data[actual_start:actual_start + length].decode('shift-jis')
            return result.strip()
        except:
            result = data[actual_start:actual_start + length].decode('shift-jis', errors='ignore')
            return result.strip()
    
    @staticmethod
    def mid_b2i(data: bytes, start: int, length: int) -> Optional[int]:
        """
        バイト配列から整数を切り出し
        
        Args:
            data: バイト配列
            start: 開始位置（1から始まる）
            length: バイト長
            
        Returns:
            整数値（変換できない場合はNone）
        """
        str_val = JVDataParser.mid_b2s(data, start, length)
        try:
            return int(str_val) if str_val else None
        except ValueError:
            return None
    
    @staticmethod
    def parse_ymd(data: bytes, start: int) -> Dict[str, str]:
        """
        年月日パース（YMD構造体）
        
        Args:
            data: バイト配列
            start: 開始位置
            
        Returns:
            年月日辞書
        """
        return {
            'year': JVDataParser.mid_b2s(data, start, 4),
            'month': JVDataParser.mid_b2s(data, start + 4, 2),
            'day': JVDataParser.mid_b2s(data, start + 6, 2),
            'formatted': JVDataParser.mid_b2s(data, start, 8)  # YYYYMMDD形式
        }
    
    @staticmethod
    def parse_hms(data: bytes, start: int) -> Dict[str, str]:
        """
        時分秒パース（HMS構造体）
        
        Args:
            data: バイト配列
            start: 開始位置
            
        Returns:
            時分秒辞書
        """
        return {
            'hour': JVDataParser.mid_b2s(data, start, 2),
            'minute': JVDataParser.mid_b2s(data, start + 2, 2),
            'second': JVDataParser.mid_b2s(data, start + 4, 2),
            'formatted': JVDataParser.mid_b2s(data, start, 6)  # HHMMSS形式
        }
    
    @staticmethod
    def parse_time(data: bytes, start: int) -> Optional[str]:
        """
        タイム（4桁）パース
        
        Args:
            data: バイト配列
            start: 開始位置
            
        Returns:
            M:SS.f形式の文字列
        """
        time_str = JVDataParser.mid_b2s(data, start, 4)
        if time_str and len(time_str) == 4:
            try:
                minutes = int(time_str[0])
                seconds = int(time_str[1:3])
                fraction = int(time_str[3])
                return f"{minutes}:{seconds:02d}.{fraction}"
            except:
                pass
        return None


class RecordParser:
    """レコード種別ごとのパーサー"""
    
    # レコード種別定義
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
        'WF': '馬体重',
        'JG': '重賞勝馬',
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
        'SK': 'SKIP',  # スキップ
        'CK': 'チェック',
    }
    
    @classmethod
    def parse(cls, data: bytes) -> Optional[Dict[str, Any]]:
        """
        レコード解析のメインメソッド
        
        Args:
            data: レコードデータ
            
        Returns:
            解析結果辞書
        """
        if len(data) < 2:
            return None
        
        record_type = data[0:2].decode('ascii', errors='ignore')
        
        # レコード種別に応じたパーサーを呼び出し
        parser_method = f'parse_{record_type.lower()}'
        if hasattr(cls, parser_method):
            return getattr(cls, parser_method)(data)
        
        # デフォルトレスポンス
        return {
            'record_type': record_type,
            'description': cls.RECORD_TYPES.get(record_type, '不明'),
            'size': len(data),
            'raw_data': data
        }
    
    @classmethod
    def parse_ra(cls, data: bytes) -> Dict[str, Any]:
        """RAレコード（レース詳細）解析"""
        parser = JVDataParser()
        
        record = {
            'record_type': 'RA',
            'description': 'レース詳細',
            'data_kubun': parser.mid_b2s(data, 3, 1),
            'make_date': parser.parse_ymd(data, 4),
            'make_time': parser.parse_hms(data, 12),
            
            # レースキー情報
            'race_key': {
                'year': parser.mid_b2s(data, 18, 4),
                'monthday': parser.mid_b2s(data, 22, 4),
                'jyo_code': parser.mid_b2s(data, 26, 2),
                'kaiji': parser.mid_b2s(data, 28, 2),
                'nichiji': parser.mid_b2s(data, 30, 2),
                'race_num': parser.mid_b2s(data, 32, 2),
            },
            
            # レース情報
            'race_info': {
                'youbi': parser.mid_b2s(data, 34, 2),
                'race_name': parser.mid_b2s(data, 36, 60),
                'fukusho_name': parser.mid_b2s(data, 96, 60),
                'kakutei_jyuni': parser.mid_b2s(data, 156, 100),
                'grade_cd': parser.mid_b2s(data, 256, 1),
                'syubetsu_cd': parser.mid_b2s(data, 257, 2),
                'kigo_cd': parser.mid_b2s(data, 259, 3),
                'jyuryo_cd': parser.mid_b2s(data, 262, 1),
                'jyoken_cd': parser.mid_b2s(data, 263, 2),
                'kyori': parser.mid_b2i(data, 266, 4),
                'track_cd': parser.mid_b2s(data, 270, 2),
                'course_kbn': parser.mid_b2s(data, 272, 1),
            },
            
            # 発走時刻
            'hassotime': parser.mid_b2s(data, 273, 4),
            
            # 頭数
            'toroku_tosu': parser.mid_b2i(data, 277, 2),
            'syusso_tosu': parser.mid_b2i(data, 279, 2),
            'nyusen_tosu': parser.mid_b2i(data, 281, 2),
            
            # 天候・馬場状態
            'condition': {
                'tenko_cd': parser.mid_b2s(data, 283, 1),
                'shiba_baba_cd': parser.mid_b2s(data, 284, 1),
                'dirt_baba_cd': parser.mid_b2s(data, 285, 1),
            },
            
            # ラップタイム（最大25個）
            'lap_time': [],
            
            # ハロンタイム
            'haron_time_s': [],
            'haron_time_l': [],
        }
        
        # ラップタイム解析（3バイト × 25）
        for i in range(25):
            lap = parser.mid_b2s(data, 286 + i*3, 3)
            if lap and lap != '000':
                record['lap_time'].append(lap)
        
        # ハロンタイムS（3バイト × 4）
        for i in range(4):
            haron = parser.mid_b2s(data, 361 + i*3, 3)
            if haron and haron != '000':
                record['haron_time_s'].append(haron)
        
        # ハロンタイムL（3バイト × 3）
        for i in range(3):
            haron = parser.mid_b2s(data, 373 + i*3, 3)
            if haron and haron != '000':
                record['haron_time_l'].append(haron)
        
        return record
    
    @classmethod
    def parse_se(cls, data: bytes) -> Dict[str, Any]:
        """SEレコード（馬毎レース情報）解析"""
        parser = JVDataParser()
        
        record = {
            'record_type': 'SE',
            'description': '馬毎レース情報',
            'data_kubun': parser.mid_b2s(data, 3, 1),
            'make_date': parser.parse_ymd(data, 4),
            
            # レースキー
            'race_key': {
                'year': parser.mid_b2s(data, 12, 4),
                'monthday': parser.mid_b2s(data, 16, 4),
                'jyo_code': parser.mid_b2s(data, 20, 2),
                'kaiji': parser.mid_b2s(data, 22, 2),
                'nichiji': parser.mid_b2s(data, 24, 2),
                'race_num': parser.mid_b2s(data, 26, 2),
            },
            
            # 馬番・血統登録番号
            'umaban': parser.mid_b2i(data, 28, 2),
            'ketto_num': parser.mid_b2s(data, 30, 10),
            
            # 馬名
            'bamei': parser.mid_b2s(data, 40, 36),
            
            # 馬情報
            'horse_info': {
                'seibetsu_cd': parser.mid_b2s(data, 76, 1),
                'barei': parser.mid_b2i(data, 77, 2),
                'tozai_cd': parser.mid_b2s(data, 79, 1),
                'hinsyu_cd': parser.mid_b2s(data, 80, 1),
                'keiro_cd': parser.mid_b2s(data, 81, 2),
            },
            
            # 馬主
            'owner': {
                'code': parser.mid_b2s(data, 83, 6),
                'name': parser.mid_b2s(data, 89, 64),
            },
            
            # 負担重量
            'futan': parser.mid_b2i(data, 153, 3),
            
            # ブリンカー
            'blinker': parser.mid_b2s(data, 156, 1),
            
            # 騎手
            'jockey': {
                'code': parser.mid_b2s(data, 157, 5),
                'name': parser.mid_b2s(data, 162, 34),
                'name_ryaku': parser.mid_b2s(data, 196, 8),
            },
            
            # 馬体重
            'bataijyu': parser.mid_b2i(data, 204, 3),
            'zogen': parser.mid_b2s(data, 207, 3),
            
            # 異常区分
            'ijyo_cd': parser.mid_b2s(data, 210, 1),
            
            # 調教師
            'trainer': {
                'code': parser.mid_b2s(data, 211, 5),
                'name': parser.mid_b2s(data, 216, 34),
                'name_ryaku': parser.mid_b2s(data, 250, 8),
                'syozoku': parser.mid_b2s(data, 258, 4),
            },
            
            # 馬主情報
            'banushi': {
                'code': parser.mid_b2s(data, 262, 6),
                'name': parser.mid_b2s(data, 268, 64),
            },
            
            # 賞金
            'prize': {
                'honsyo': parser.mid_b2i(data, 332, 8),
                'fukasyo': parser.mid_b2i(data, 340, 8),
                'shutokujyo': parser.mid_b2i(data, 348, 8),
                'shutoku': parser.mid_b2i(data, 356, 8),
            },
            
            # レース結果
            'result': {
                'kakutei_jyuni': parser.mid_b2i(data, 364, 2),
                'time': parser.parse_time(data, 366),
                'chakusa_cd': parser.mid_b2s(data, 370, 1),
                'chakusa': parser.mid_b2s(data, 371, 3),
                'jyuni_fuka': parser.mid_b2s(data, 374, 1),
                'tansho_odds': parser.mid_b2i(data, 375, 4),
                'ninsiki': parser.mid_b2i(data, 379, 2),
            },
        }
        
        return record
    
    @classmethod
    def parse_um(cls, data: bytes) -> Dict[str, Any]:
        """UMレコード（競走馬マスタ）解析"""
        parser = JVDataParser()
        
        record = {
            'record_type': 'UM',
            'description': '競走馬マスタ',
            'data_kubun': parser.mid_b2s(data, 3, 1),
            'make_date': parser.parse_ymd(data, 4),
            
            # 血統登録番号
            'ketto_num': parser.mid_b2s(data, 12, 10),
            
            # 削除区分
            'del_kubun': parser.mid_b2s(data, 22, 1),
            
            # 登録・抹消日
            'touroku_date': parser.parse_ymd(data, 23),
            'massyo_date': parser.parse_ymd(data, 31),
            
            # 馬名
            'bamei': parser.mid_b2s(data, 39, 36),
            
            # 生年月日
            'birth_date': parser.parse_ymd(data, 75),
            
            # 馬情報
            'horse_info': {
                'seibetsu_cd': parser.mid_b2s(data, 83, 1),
                'hinsyu_cd': parser.mid_b2s(data, 84, 1),
                'keiro_cd': parser.mid_b2s(data, 85, 2),
            },
            
            # 系統
            'keito': parser.mid_b2s(data, 87, 60),
            
            # 3代血統
            'blood': {
                'father': parser.mid_b2s(data, 147, 10),
                'mother': parser.mid_b2s(data, 157, 10),
                'bms': parser.mid_b2s(data, 167, 10),  # 母父
            },
            
            # 東西所属
            'tozai_cd': parser.mid_b2s(data, 177, 1),
            
            # 調教師
            'trainer': {
                'code': parser.mid_b2s(data, 178, 5),
                'name': parser.mid_b2s(data, 183, 34),
            },
            
            # 馬主
            'banushi': {
                'code': parser.mid_b2s(data, 217, 6),
                'name': parser.mid_b2s(data, 223, 64),
            },
            
            # 生産者
            'breeder': {
                'code': parser.mid_b2s(data, 287, 6),
                'name': parser.mid_b2s(data, 293, 42),
            },
            
            # 産地名
            'sanchi_name': parser.mid_b2s(data, 335, 20),
        }
        
        return record
    
    @classmethod
    def parse_o1(cls, data: bytes) -> Dict[str, Any]:
        """O1レコード（単複オッズ）解析"""
        parser = JVDataParser()
        
        record = {
            'record_type': 'O1',
            'description': '単複オッズ',
            'data_kubun': parser.mid_b2s(data, 3, 1),
            'make_date': parser.parse_ymd(data, 4),
            
            # レースキー
            'race_key': {
                'year': parser.mid_b2s(data, 12, 4),
                'monthday': parser.mid_b2s(data, 16, 4),
                'jyo_code': parser.mid_b2s(data, 20, 2),
                'kaiji': parser.mid_b2s(data, 22, 2),
                'nichiji': parser.mid_b2s(data, 24, 2),
                'race_num': parser.mid_b2s(data, 26, 2),
            },
            
            # 発売票数合計
            'total_sale': {
                'tansho': parser.mid_b2s(data, 28, 11),
                'fukusho': parser.mid_b2s(data, 39, 11),
            },
            
            # 返還総額
            'henkan': {
                'tansho': parser.mid_b2s(data, 50, 11),
                'fukusho': parser.mid_b2s(data, 61, 11),
            },
            
            # オッズ（最大28頭分）
            'odds': [],
        }
        
        # 各馬のオッズ情報（16バイト × 28頭）
        for i in range(28):
            base_pos = 72 + i * 16
            
            umaban = parser.mid_b2i(data, base_pos, 2)
            if umaban and umaban > 0:
                horse_odds = {
                    'umaban': umaban,
                    'tansho_odds': parser.mid_b2i(data, base_pos + 2, 4),
                    'fukusho_odds_low': parser.mid_b2i(data, base_pos + 6, 4),
                    'fukusho_odds_high': parser.mid_b2i(data, base_pos + 10, 4),
                    'tansho_ninki': parser.mid_b2i(data, base_pos + 14, 1),
                    'fukusho_ninki': parser.mid_b2i(data, base_pos + 15, 1),
                }
                record['odds'].append(horse_odds)
        
        return record
    
    @classmethod
    def parse_wf(cls, data: bytes) -> Dict[str, Any]:
        """WFレコード（馬体重）解析"""
        parser = JVDataParser()
        
        record = {
            'record_type': 'WF',
            'description': '馬体重',
            'data_kubun': parser.mid_b2s(data, 3, 1),
            'make_date': parser.parse_ymd(data, 4),
            
            # レースキー
            'race_key': {
                'year': parser.mid_b2s(data, 12, 4),
                'monthday': parser.mid_b2s(data, 16, 4),
                'jyo_code': parser.mid_b2s(data, 20, 2),
                'kaiji': parser.mid_b2s(data, 22, 2),
                'nichiji': parser.mid_b2s(data, 24, 2),
                'race_num': parser.mid_b2s(data, 26, 2),
            },
            
            # 馬体重情報（最大28頭分）
            'weights': [],
        }
        
        # 各馬の馬体重情報（7バイト × 28頭）
        for i in range(28):
            base_pos = 28 + i * 7
            
            umaban = parser.mid_b2i(data, base_pos, 2)
            if umaban and umaban > 0:
                weight_info = {
                    'umaban': umaban,
                    'bataijyu': parser.mid_b2i(data, base_pos + 2, 3),
                    'zogen_fuka': parser.mid_b2s(data, base_pos + 5, 1),
                    'zogen': parser.mid_b2s(data, base_pos + 6, 3),
                }
                record['weights'].append(weight_info)
        
        return record
    
    @classmethod
    def parse_ys(cls, data: bytes) -> Dict[str, Any]:
        """YSレコード（年間スケジュール）解析"""
        parser = JVDataParser()
        
        record = {
            'record_type': 'YS',
            'description': '年間スケジュール',
            'data_kubun': parser.mid_b2s(data, 3, 1),
            'make_date': parser.parse_ymd(data, 4),
            
            # 年
            'year': parser.mid_b2s(data, 12, 4),
            
            # 変更識別
            'henko_id': parser.mid_b2s(data, 16, 1),
            
            # 開催情報
            'kaisai_info': []
        }
        
        # 開催情報（最大397開催）
        for i in range(397):
            base_pos = 17 + i * 16
            if base_pos + 16 > len(data):
                break
            
            # 開催キー
            kaiji_date = parser.mid_b2s(data, base_pos, 8)
            if kaiji_date and kaiji_date != '00000000':
                kaisai = {
                    'kaiji_date': kaiji_date,
                    'jyo_code': parser.mid_b2s(data, base_pos + 8, 2),
                    'kaiji': parser.mid_b2s(data, base_pos + 10, 2),
                    'nichiji': parser.mid_b2s(data, base_pos + 12, 2),
                    'youbi': parser.mid_b2s(data, base_pos + 14, 2),
                }
                record['kaisai_info'].append(kaisai)
        
        return record


class CodeMaster:
    """各種コードマスタ定義"""
    
    # 競馬場コード
    JYO_CODE = {
        '01': '札幌',
        '02': '函館',
        '03': '福島',
        '04': '新潟',
        '05': '東京',
        '06': '中山',
        '07': '中京',
        '08': '京都',
        '09': '阪神',
        '10': '小倉',
    }
    
    # グレードコード
    GRADE_CODE = {
        'A': 'G1',
        'B': 'G2',
        'C': 'G3',
        ' ': '平場',
    }
    
    # 種別コード
    SYUBETSU_CODE = {
        '11': '2歳',
        '12': '3歳',
        '13': '3歳以上',
        '14': '4歳以上',
        '18': '障害',
    }
    
    # トラックコード
    TRACK_CODE = {
        '00': '芝',
        '10': '芝外',
        '11': '芝内-外',
        '12': '芝外-内',
        '17': '芝内2周',
        '18': '芝外2周',
        '19': 'ダート',
        '20': 'ダート',
        '21': 'ダ内-外',
        '22': 'ダ外-内',
        '23': 'ダ内2周',
        '24': 'ダ外2周',
        '29': 'ダート',
        '51': '障芝',
        '52': '障芝ダ',
        '53': '障ダ芝',
        '54': '障害ダ',
        '55': '障直線',
        '56': '障芝外',
        '57': '障芝内-外',
        '58': '障芝外-内',
        '59': '障芝内2周',
    }
    
    # 天候コード
    TENKO_CODE = {
        '1': '晴',
        '2': '曇',
        '3': '雨',
        '4': '小雨',
        '5': '雪',
        '6': '小雪',
    }
    
    # 芝馬場状態コード
    SHIBA_BABA_CODE = {
        '1': '良',
        '2': '稍重',
        '3': '重',
        '4': '不良',
    }
    
    # ダート馬場状態コード
    DIRT_BABA_CODE = {
        '1': '良',
        '2': '稍重',
        '3': '重',
        '4': '不良',
    }
    
    # 性別コード
    SEIBETSU_CODE = {
        '1': '牡',
        '2': '牝',
        '3': 'セ',
    }
    
    # 品種コード
    HINSYU_CODE = {
        '1': 'サラ',
        '2': 'アラ',
    }
    
    # 毛色コード
    KEIRO_CODE = {
        '01': '栗毛',
        '02': '栃栗毛',
        '03': '鹿毛',
        '04': '黒鹿毛',
        '05': '青鹿毛',
        '06': '青毛',
        '07': '芦毛',
        '08': '栗粕毛',
        '09': '鹿粕毛',
        '10': '青粕毛',
        '11': '白毛',
    }
    
    # 東西所属コード
    TOZAI_CODE = {
        '1': '美浦',
        '2': '栗東',
        '3': '地方',
        '4': '海外',
    }
    
    # 異常区分コード
    IJYO_CODE = {
        '0': '異常なし',
        '1': '取消',
        '2': '発走除外',
        '3': '競走除外',
        '4': '競走中止',
        '5': '失格',
        '6': '落馬再騎乗',
        '7': '降着',
    }
    
    @classmethod
    def get_name(cls, code_type: str, code: str) -> str:
        """
        コードから名称を取得
        
        Args:
            code_type: コード種別
            code: コード値
            
        Returns:
            名称（見つからない場合はコードそのまま）
        """
        code_dict = getattr(cls, code_type.upper() + '_CODE', None)
        if code_dict:
            return code_dict.get(code, code)
        return code


def test_parser():
    """パーサーのテスト"""
    print("JV-Dataパーサーテスト")
    print("=" * 50)
    
    # テストデータ（実際のデータが必要）
    test_data = b'RA' + b'1' + b'20250101' + b'120000' + b' ' * 1000
    
    # レコード解析
    result = RecordParser.parse(test_data)
    
    if result:
        print(f"レコード種別: {result.get('record_type')}")
        print(f"説明: {result.get('description')}")
        print(f"データサイズ: {result.get('size', len(test_data))}バイト")
    
    print("=" * 50)
    print("テスト完了")


if __name__ == "__main__":
    test_parser()