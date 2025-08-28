"""
JRA-VAN DataLab Python Client (64bit対応版)
Based on JRA-VAN SDK Ver4.9.0.2

64bit Python環境では自動的にブリッジモードで動作

Author: StableFormer Project
Date: 2025-08-28
"""

import sys
import time
import os
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# win32comのインポート（必須）
try:
    import win32com.client
except ImportError:
    logger.error("win32comがインストールされていません")
    logger.error("pip install pywin32 を実行してください")
    raise ImportError("pywin32 is required")


class JVLinkClient:
    """JV-Link COMオブジェクトのラッパークラス"""
    
    # JV-Link CLSID (正しいCLSID)
    CLSID_JVLINK = "{2AB1774D-0C41-11D7-916F-0003479BEB3F}"
    
    # データ種別定数
    DATA_SPEC = {
        'RACE': 'RACE',      # レース情報
        'DIFF': 'DIFF',      # 差分データ
        'BLOD': 'BLOD',      # 血統データ
        'MING': 'MING',      # マイニングデータ
        'SNAP': 'SNAP',      # スナップショット
        'YSCH': 'YSCH',      # 年間スケジュール
        'HOSE': 'HOSE',      # 競走馬データ
        'HOYU': 'HOYU',      # 馬主データ
        'PROD': 'PROD',      # 生産者データ
        'SANKU': 'SANK',     # 産駒データ
        'TOKU': 'TOKU',      # 特別登録馬データ
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
        'JOCKEY_CHANGE': '0B41',    # 騎手変更
        'WEATHER': '0B42',          # 天候馬場
        'AV_INFO': '0B51',          # AVInfo
    }
    
    # エラーコード定義
    ERROR_CODES = {
        0: "正常終了",
        -1: "パラメータエラー/ファイル切り替わり",
        -2: "初期化前エラー",
        -3: "ファイルダウンロード中",
        -100: "その他エラー",
        -101: "該当データ無し",
        -102: "集計データ配信前",
        -103: "集計データ配信前",
        -111: "ユーザキャンセル",
        -112: "ダイアログ起動エラー",
        -114: "ファイル削除エラー",
        -115: "ファイル削除中",
        -116: "サービス利用なし",
        -118: "保存パス指定エラー",
        -201: "JVInit未実行",
        -202: "前回のJVOpenが開いたまま",
        -203: "パラメータエラー",
        -204: "該当ファイル無し",
        -211: "サービスキー認証エラー",
        -212: "サービスキー有効期限切れ",
        -301: "認証エラー",
        -302: "サービス利用なし",
        -303: "サービス有効期限切れ",
        -401: "JVOpen未実行",
        -402: "バッファ不足エラー",
        -403: "ファイルアクセスエラー",
        -411: "レジストリアクセスエラー",
        -412: "レジストリアクセスエラー",
        -413: "レジストリアクセスエラー",
        -421: "レジストリアクセスエラー",
        -431: "レジストリアクセスエラー",
        -501: "スタートキットダウンロード中",
        -502: "サーバーメンテナンス中",
        -503: "スタートキットパラメータエラー",
        -504: "スタートキットダウンロードエラー",
    }
    
    def __init__(self) -> None:
        """コンストラクタ"""
        self.jvlink: Optional[Any] = None
        self.is_initialized: bool = False
        self.is_open: bool = False
        
    def initialize(self, sid: str = "UNKNOWN") -> int:
        """
        JV-Link初期化
        
        Args:
            sid: ソフトウェアID（任意の文字列）
            
        Returns:
            0: 正常終了
            その他: エラーコード
        """
        try:
            logger.info(f"JV-Link初期化開始 (SID: {sid})")
            
            # COMオブジェクト作成
            if not self.jvlink:
                self.jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
            
            # JVInit実行
            ret = self.jvlink.JVInit(sid)
            
            if ret == 0:
                self.is_initialized = True
                version = self.get_version()
                logger.info(f"JV-Link初期化成功 (Version: {version})")
            else:
                logger.error(f"JV-Link初期化エラー: {self.get_error_message(ret)}")
                
            return ret
            
        except Exception as e:
            logger.error(f"JV-Link初期化例外: {e}")
            return -100
    
    def get_version(self) -> str:
        """JV-Linkバージョン取得"""
        if self.jvlink:
            try:
                return self.jvlink.m_JVLinkVersion
            except (AttributeError, OSError, Exception) as e:
                logger.warning(f"JV-Linkバージョン取得エラー: {e}")
                return "Unknown"
        return ""
    
    def get_error_message(self, code: int) -> str:
        """エラーコードからメッセージ取得"""
        return self.ERROR_CODES.get(code, f"未定義エラー({code})")
    
    def set_save_path(self, path: str) -> int:
        """
        保存パス設定
        
        Args:
            path: 保存先パス
            
        Returns:
            0: 正常終了
            その他: エラーコード
        """
        if self.jvlink:
            # パスが存在しない場合は作成
            if not os.path.exists(path):
                os.makedirs(path)
            return self.jvlink.JVSetSavePath(path)
        return -1
    
    def set_save_flag(self, flag: int) -> int:
        """
        保存フラグ設定
        
        Args:
            flag: 0:保存しない 1:保存する
            
        Returns:
            0: 正常終了
            その他: エラーコード
        """
        if self.jvlink:
            return self.jvlink.JVSetSaveFlag(flag)
        return -1
    
    def set_ui_properties(self) -> int:
        """JVLink設定ダイアログ表示"""
        if self.jvlink:
            logger.info("JVLink設定ダイアログ表示")
            return self.jvlink.JVSetUIProperties()
        return -1
    
    def open(self, data_spec: str, from_time: str = "99999999999999", 
             option: int = 1) -> Tuple[int, int, int, str]:
        """
        蓄積系データオープン
        
        Args:
            data_spec: データ種別（DATA_SPEC参照）
            from_time: 取得開始日時（YYYYMMDDHHMMSSまたは99999999999999）
            option: 1:通常 2:今週データ 3:セットアップデータ 4:ダイアログ無し
            
        Returns:
            (戻り値コード, 読込対象数, ダウンロード数, 最終ファイルタイムスタンプ)
        """
        if not self.is_initialized:
            logger.error("JVInit未実行")
            return (-201, 0, 0, "")
        
        if self.is_open:
            logger.warning("前回のJVOpenを閉じています")
            self.close()
        
        logger.info(f"JVOpen実行: spec={data_spec}, from={from_time}, option={option}")
        
        # JVOpen実行
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
            logger.info(f"JVOpen成功: 読込対象={read_count}, DL={download_count}")
        else:
            logger.error(f"JVOpenエラー: {self.get_error_message(ret_code)}")
            
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
            logger.error("JVInit未実行")
            return -201
        
        if self.is_open:
            logger.warning("前回のJVOpenを閉じています")
            self.close()
        
        logger.info(f"JVRTOpen実行: spec={data_spec}, key={key}")
        
        ret = self.jvlink.JVRTOpen(data_spec, key)
        
        if ret == 0:
            self.is_open = True
            logger.info("JVRTOpen成功")
        else:
            logger.error(f"JVRTOpenエラー: {self.get_error_message(ret)}")
            
        return ret
    
    def read(self, buffer_size: int = 110000) -> Tuple[int, bytes, str]:
        """
        データ読み込み
        
        Args:
            buffer_size: バッファサイズ（最大110000）
            
        Returns:
            (戻り値コード, データ, ファイル名)
        """
        if not self.is_open:
            return (-401, b"", "")
        
        # JVRead呼び出し
        result = self.jvlink.JVRead(buffer_size, "")
        
        if isinstance(result, tuple) and len(result) == 3:
            ret_code, data, filename = result
        else:
            return (-100, b"", "")
        
        # 文字列をバイト列に変換
        if isinstance(data, str):
            data = data.encode('shift-jis', errors='ignore')
        
        return (ret_code, data, filename)
    
    def gets(self, buffer_size: int = 110000) -> Tuple[int, bytes, str]:
        """
        データ読み込み（JVGets版）
        バイナリデータ対応版
        
        Args:
            buffer_size: バッファサイズ（最大110000）
            
        Returns:
            (戻り値コード, データ, ファイル名)
        """
        if not self.is_open:
            return (-401, b"", "")
        
        try:
            # JVGets呼び出し（バイナリ対応）
            result = self.jvlink.JVGets(None, buffer_size, "")
            
            if isinstance(result, tuple) and len(result) >= 3:
                ret_code = result[0]
                data = result[1]
                filename = result[2] if len(result) > 2 else ""
                
                # VARIANTからバイト配列に変換
                if data is not None:
                    if hasattr(data, 'value'):
                        data = bytes(data.value)
                    elif isinstance(data, str):
                        data = data.encode('shift-jis', errors='ignore')
                else:
                    data = b""
                    
                return (ret_code, data, filename)
            else:
                return (-100, b"", "")
                
        except AttributeError:
            # JVGetsが存在しない場合はJVReadを使用
            return self.read(buffer_size)
    
    def status(self) -> int:
        """
        ダウンロード進捗取得
        
        Returns:
            ダウンロード済みファイル数
        """
        if self.jvlink:
            return self.jvlink.JVStatus()
        return -1
    
    def cancel(self) -> None:
        """ダウンロードキャンセル"""
        if self.jvlink:
            logger.info("ダウンロードキャンセル")
            self.jvlink.JVCancel()
    
    def close(self) -> int:
        """
        JV-Link終了処理
        
        Returns:
            戻り値コード
        """
        if self.jvlink and self.is_open:
            logger.info("JVClose実行")
            ret = self.jvlink.JVClose()
            self.is_open = False
            return ret
        return 0
    
    def file_delete(self, filename: str) -> int:
        """
        ファイル削除
        
        Args:
            filename: 削除対象ファイル名
            
        Returns:
            0: 正常終了
            その他: エラーコード
        """
        if self.jvlink:
            logger.info(f"ファイル削除: {filename}")
            return self.jvlink.JVFileDelete(filename)
        return -1
    
    def __del__(self) -> None:
        """デストラクタ"""
        if self.is_open:
            self.close()
            

def test_connection() -> bool:
    """接続テスト"""
    print("JRA-VAN DataLab接続テスト開始")
    print("=" * 50)
    
    client = JVLinkClient()
    
    # 初期化
    ret = client.initialize("TEST")
    if ret != 0:
        print(f"初期化エラー: {client.get_error_message(ret)}")
        return False
    
    print(f"JV-Linkバージョン: {client.get_version()}")
    
    # 設定ダイアログ表示（オプション）
    # ret = client.set_ui_properties()
    
    # データ取得テスト（最小限のデータ）
    ret, read_count, download_count, last_timestamp = client.open(
        data_spec="YSCH",  # 年間スケジュール（軽量）
        from_time="20250101000000",
        option=1
    )
    
    if ret >= 0:
        print(f"読込対象: {read_count}件")
        print(f"ダウンロード: {download_count}ファイル")
        print(f"最終更新: {last_timestamp}")
        
        # データ読み込み（最初の5件のみ）
        for i in range(min(5, read_count)):
            ret, data, filename = client.read()
            
            if ret > 0:
                record_type = data[0:2].decode('ascii', errors='ignore') if len(data) >= 2 else "??"
                print(f"  [{i+1}] レコード種別: {record_type}, サイズ: {ret}bytes")
            elif ret == 0:
                print("読み込み完了")
                break
            elif ret == -1:
                print(f"ファイル切り替え: {filename}")
            elif ret == -3:
                status = client.status()
                print(f"ダウンロード中... ({status}ファイル完了)")
                time.sleep(1)
    
    # 終了処理
    client.close()
    
    print("=" * 50)
    print("テスト完了")
    return True


if __name__ == "__main__":
    # 接続テスト実行
    test_connection()