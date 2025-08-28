# JRA-VAN DataLab API 実装ガイド

## 概要
このドキュメントは、JRA-VAN DataLabのJV-Link APIを使用してPythonおよびC言語で競馬データを取得する詳細な実装方法をまとめたものです。

## JV-Link API概要

### 最新仕様 (2024年8月7日更新)
- **JV-Link インターフェース仕様書**: Ver.4.9.0.1
- **JV-Data 仕様書**: Ver.4.9.0.1 (PDF版・Excel版)
- **提供形態**: ActiveX COMコントロール（32ビット版のみ）

### APIの基本構成
JV-LinkはJRA-VAN DataLabサービスを利用するためのインターフェースモジュールで、競馬ソフトはJV-LinkおよびJV-Dataサーバから各種競馬データを取得します。

## 主要メソッド詳細

### 1. JVInit (初期化)
```
JVInit(sid)
```
- **用途**: JV-Linkの初期化
- **パラメータ**: 
  - `sid`: ソフトウェア識別文字列（"UNKNOWN"や任意の文字列）
- **呼び出しタイミング**: JVOpenを使用する前に最低1回呼び出す必要がある

### 2. JVOpen (データ読み込み準備)
```
JVOpen(dataSpec, fromTime, option, readCount, downloadCount, lastFileTimestamp)
```
- **用途**: 蓄積系データの読み込み準備
- **パラメータ**:
  - `dataSpec`: データ種別（例: "RACE", "0B12" など）
  - `fromTime`: データ提供日時（YYYYMMDDHHMMSSまたは"99999999999999"）
  - `option`: オプションフラグ（1:通常、2:今週データ、3:セットアップデータ）
  - `readCount`: 読み込み対象レコード数（戻り値）
  - `downloadCount`: ダウンロードファイル数（戻り値）
  - `lastFileTimestamp`: 最新ファイルのタイムスタンプ（戻り値）
- **戻り値**: 0以上で正常終了、負数でエラー

### 3. JVRTOpen (リアルタイムデータ取得)
```
JVRTOpen(dataSpec, key)
```
- **用途**: 速報系データの読み込み準備
- **パラメータ**:
  - `dataSpec`: データ種別（例: "0B12", "0B15"など）
  - `key`: レースキーまたは空文字列

### 4. JVRead (データ読み込み)
```
JVRead(buffer, size, filename)
```
- **用途**: JV-Dataをレコード単位で読み込み
- **パラメータ**:
  - `buffer`: 読み込んだデータを格納するバッファ
  - `size`: バッファサイズ
  - `filename`: 現在読み込み中のファイル名（戻り値）
- **戻り値**:
  - 正数: 読み込んだバイト数
  - 0: 全ファイル読み込み終了
  - -1: ファイル切り替わり
  - -3: ファイルダウンロード中
  - 負数: 各種エラー

### 5. JVStatus (ダウンロード進捗確認)
```
JVStatus()
```
- **用途**: JVOpenで開始したダウンロードの進捗確認
- **戻り値**: ダウンロード済みファイル数

### 6. JVClose (終了処理)
```
JVClose()
```
- **用途**: JV-Linkの終了処理

## Python実装

### 環境準備

#### 32ビット版Python使用時
```bash
# 32ビット版Pythonをインストール
# pywin32パッケージをインストール
pip install pywin32
```

#### 64ビット版Python使用時（DLLサロゲート方式）
レジストリ設定により、64ビットPythonから32ビットDLLを使用可能にする方法があります。

### 基本実装例

```python
import win32com.client
import time
import struct

class JVLinkReader:
    def __init__(self):
        # COMオブジェクトの作成
        self.jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
        
    def initialize(self, sid="UNKNOWN"):
        """JV-Linkの初期化"""
        ret = self.jvlink.JVInit(sid)
        if ret != 0:
            raise Exception(f"JVInit failed with code: {ret}")
        print("JV-Link initialized successfully")
        
    def open_data(self, data_spec="RACE", from_time="20240101000000", option=1):
        """データ読み込みの準備
        
        Args:
            data_spec: データ種別（RACE, DIFF, BLODなど）
            from_time: 取得開始日時（YYYYMMDDHHMMSSまたは99999999999999）
            option: 1:通常 2:今週データ 3:セットアップデータ
        """
        # pywin32では戻り値を受け取る引数はダミー値を渡す
        result = self.jvlink.JVOpen(data_spec, from_time, option, 0, 0, "")
        
        if len(result) == 4:
            ret_code, read_count, download_count, last_timestamp = result
        else:
            ret_code = result
            read_count = download_count = 0
            last_timestamp = ""
            
        if ret_code < 0:
            raise Exception(f"JVOpen failed with code: {ret_code}")
            
        print(f"JVOpen successful:")
        print(f"  Read count: {read_count}")
        print(f"  Download count: {download_count}")
        print(f"  Last timestamp: {last_timestamp}")
        
        return read_count, download_count
        
    def read_data(self, max_records=100):
        """データの読み込み
        
        Args:
            max_records: 読み込む最大レコード数
        """
        buffer_size = 110000  # 最大レコードサイズ
        records = []
        
        for i in range(max_records):
            # データ読み込み
            result = self.jvlink.JVRead(buffer_size, "")
            
            if len(result) == 3:
                ret_code, data, filename = result
            else:
                ret_code = result
                data = ""
                filename = ""
                
            if ret_code > 0:
                # 正常にデータを読み込めた
                record_type = data[0:2] if len(data) >= 2 else ""
                records.append({
                    'type': record_type,
                    'data': data,
                    'size': ret_code,
                    'filename': filename
                })
                
            elif ret_code == 0:
                # 全データ読み込み完了
                print("All data read completed")
                break
                
            elif ret_code == -1:
                # ファイル切り替わり
                print(f"File switched: {filename}")
                continue
                
            elif ret_code == -3:
                # ダウンロード中
                print("Downloading... waiting")
                time.sleep(1)
                status = self.jvlink.JVStatus()
                print(f"Download status: {status}")
                continue
                
            else:
                # エラー
                print(f"JVRead error: {ret_code}")
                break
                
        return records
        
    def read_realtime(self, data_spec="0B12", key=""):
        """リアルタイムデータの読み込み
        
        Args:
            data_spec: データ種別（0B12:オッズ、0B15:馬体重など）
            key: レースキー（空文字列で当日全レース）
        """
        # リアルタイムデータオープン
        ret = self.jvlink.JVRTOpen(data_spec, key)
        if ret != 0:
            raise Exception(f"JVRTOpen failed with code: {ret}")
            
        # データ読み込み
        return self.read_data()
        
    def close(self):
        """終了処理"""
        ret = self.jvlink.JVClose()
        if ret != 0:
            print(f"JVClose warning: {ret}")
        print("JV-Link closed")
        
    def parse_race_data(self, data):
        """レースデータ（RA）のパース例
        
        固定長データの解析例
        """
        if not data.startswith("RA"):
            return None
            
        # RAレコードの一部フィールド解析例
        # 実際の仕様書に基づいて位置を調整する必要があります
        parsed = {
            'record_type': data[0:2],      # レコード種別
            'record_key': data[2:12],      # レコードキー
            'race_date': data[12:20],      # 開催年月日
            'course_code': data[20:22],    # 競馬場コード
            'race_number': data[22:24],    # レース番号
            'race_name': data[24:84].strip(),  # レース名（全角30文字）
            'distance': data[84:88],       # 距離
            'track_code': data[88:90],     # トラックコード
        }
        
        return parsed

# 使用例
def main():
    reader = JVLinkReader()
    
    try:
        # 初期化
        reader.initialize()
        
        # データ取得（2024年1月以降のレースデータ）
        read_count, download_count = reader.open_data(
            data_spec="RACE",
            from_time="20240101000000",
            option=1
        )
        
        # データ読み込み
        records = reader.read_data(max_records=10)
        
        # レコード解析
        for record in records:
            if record['type'] == 'RA':  # レースデータ
                parsed = reader.parse_race_data(record['data'])
                if parsed:
                    print(f"Race: {parsed['race_name']} ({parsed['race_date']})")
                    
    finally:
        # 終了処理
        reader.close()

if __name__ == "__main__":
    main()
```

### Python実装の注意点

1. **32ビット制限**: JV-Linkは32ビット版のみのため、通常は32ビット版Pythonが必要
2. **戻り値の扱い**: pywin32使用時、出力パラメータはタプルとして返される
3. **文字コード**: JV-Dataは主にShift-JISエンコーディング
4. **バッファサイズ**: レコード種別により最大サイズが異なる（最大約110KB）

## C#実装例

### 環境準備
1. Visual Studioプロジェクトで「COM参照」を追加
2. 「JRA-VAN Data Lab 1.1.8 Type Library」を選択

### 基本実装例

```csharp
using System;
using JVDTLabLib;

public class JVLinkReader
{
    private JVLinkClass jvLink;
    
    public JVLinkReader()
    {
        jvLink = new JVLinkClass();
    }
    
    public void Initialize(string sid = "UNKNOWN")
    {
        int ret = jvLink.JVInit(sid);
        if (ret != 0)
        {
            throw new Exception($"JVInit failed: {ret}");
        }
        Console.WriteLine("JV-Link initialized");
    }
    
    public void OpenData(string dataSpec = "RACE", 
                         string fromTime = "20240101000000", 
                         int option = 1)
    {
        int readCount = 0;
        int downloadCount = 0;
        string lastTimestamp = "";
        
        int ret = jvLink.JVOpen(dataSpec, fromTime, option, 
                                ref readCount, ref downloadCount, 
                                ref lastTimestamp);
        
        if (ret < 0)
        {
            throw new Exception($"JVOpen failed: {ret}");
        }
        
        Console.WriteLine($"Read count: {readCount}");
        Console.WriteLine($"Download count: {downloadCount}");
        Console.WriteLine($"Last timestamp: {lastTimestamp}");
    }
    
    public void ReadData(int maxRecords = 100)
    {
        string buffer = new string(' ', 110000);
        string filename = "";
        
        for (int i = 0; i < maxRecords; i++)
        {
            int ret = jvLink.JVRead(ref buffer, buffer.Length, ref filename);
            
            if (ret > 0)
            {
                // データ読み込み成功
                string recordType = buffer.Substring(0, 2);
                Console.WriteLine($"Record type: {recordType}, Size: {ret}");
                
                // レコード種別に応じて処理
                ProcessRecord(recordType, buffer.Substring(0, ret));
            }
            else if (ret == 0)
            {
                // 全データ読み込み完了
                Console.WriteLine("All data read completed");
                break;
            }
            else if (ret == -1)
            {
                // ファイル切り替わり
                Console.WriteLine($"File switched: {filename}");
            }
            else if (ret == -3)
            {
                // ダウンロード中
                System.Threading.Thread.Sleep(1000);
                int status = jvLink.JVStatus();
                Console.WriteLine($"Download status: {status}");
            }
            else
            {
                // エラー
                Console.WriteLine($"JVRead error: {ret}");
                break;
            }
        }
    }
    
    private void ProcessRecord(string recordType, string data)
    {
        switch (recordType)
        {
            case "RA":  // レースデータ
                ProcessRaceData(data);
                break;
            case "SE":  // 馬毎レース情報
                ProcessHorseRaceData(data);
                break;
            case "UM":  // 競走馬マスタ
                ProcessHorseMaster(data);
                break;
            // 他のレコード種別も同様に処理
        }
    }
    
    private void ProcessRaceData(string data)
    {
        // RAレコードの解析例
        var raceData = new
        {
            RecordType = data.Substring(0, 2),
            RecordKey = data.Substring(2, 10),
            RaceDate = data.Substring(12, 8),
            CourseCode = data.Substring(20, 2),
            RaceNumber = data.Substring(22, 2),
            RaceName = data.Substring(24, 60).Trim()
        };
        
        Console.WriteLine($"Race: {raceData.RaceName} ({raceData.RaceDate})");
    }
    
    private void ProcessHorseRaceData(string data)
    {
        // SEレコードの解析
        // 実装省略
    }
    
    private void ProcessHorseMaster(string data)
    {
        // UMレコードの解析
        // 実装省略
    }
    
    public void Close()
    {
        int ret = jvLink.JVClose();
        if (ret != 0)
        {
            Console.WriteLine($"JVClose warning: {ret}");
        }
        Console.WriteLine("JV-Link closed");
    }
}

// 使用例
class Program
{
    static void Main()
    {
        var reader = new JVLinkReader();
        
        try
        {
            reader.Initialize();
            reader.OpenData("RACE", "20240101000000", 1);
            reader.ReadData(100);
        }
        finally
        {
            reader.Close();
        }
    }
}
```

## JV-Dataレコード種別

### 主要なレコード種別
| レコード種別 | 説明 | 最大サイズ |
|------------|------|-----------|
| RA | レース詳細 | 約1KB |
| SE | 馬毎レース情報 | 約2KB |
| HR | 払戻 | 約10KB |
| H1 | 単勝オッズ | 約15KB |
| H6 | 3連単オッズ | 約100KB |
| O1 | 単複オッズ | 約1KB |
| O2 | 馬連オッズ | 約10KB |
| O3 | ワイドオッズ | 約10KB |
| O4 | 馬単オッズ | 約20KB |
| O5 | 3連複オッズ | 約30KB |
| O6 | 3連単オッズ | 約100KB |
| UM | 競走馬マスタ | 約5KB |
| KS | 騎手マスタ | 約1KB |
| CH | 調教師マスタ | 約1KB |
| BR | 生産者マスタ | 約1KB |
| BN | 馬主マスタ | 約1KB |

## データ種別コード

### 蓄積系データ
| コード | 説明 | 更新タイミング |
|-------|------|-------------|
| RACE | レース情報 | レース確定後 |
| DIFF | 差分データ | リアルタイム |
| BLOD | 血統データ | 随時 |
| MING | マイニングデータ | 週次 |
| SNAP | スナップショットデータ | 日次 |
| YSCH | 開催スケジュール | 随時 |

### 速報系データ
| コード | 説明 | 提供タイミング |
|-------|------|-------------|
| 0B12 | オッズ（単複枠） | 発売中随時 |
| 0B13 | オッズ（馬連） | 発売中随時 |
| 0B14 | オッズ（ワイド） | 発売中随時 |
| 0B15 | 馬体重 | 発表後 |
| 0B16 | オッズ（馬単） | 発売中随時 |
| 0B17 | オッズ（3連複） | 発売中随時 |
| 0B18 | オッズ（3連単） | 発売中随時 |
| 0B20 | 速報成績 | レース確定後 |
| 0B30 | 票数（全賭式） | 確定後 |

## エラーコード一覧

### JVInit
| コード | 説明 |
|-------|------|
| 0 | 正常終了 |
| -1 | 初期化失敗 |

### JVOpen/JVRTOpen
| コード | 説明 |
|-------|------|
| 0以上 | 正常終了 |
| -1 | パラメータエラー |
| -2 | 初期化前エラー |
| -3 | 認証エラー |
| -201 | JVInit未実行 |
| -202 | 前回のJVOpen/JVRTOpenが開いたまま |
| -203 | パラメータエラー |
| -211 | サービスキー認証エラー |

### JVRead
| コード | 説明 |
|-------|------|
| 正数 | 読み込んだバイト数 |
| 0 | 全ファイル読み込み終了 |
| -1 | ファイル切り替わり |
| -3 | ファイルダウンロード中 |
| -201 | JVOpen/JVRTOpen未実行 |
| -202 | バッファサイズ不足 |
| -203 | ファイルが見つからない |
| -403 | サーバーメンテナンス中 |
| -502 | サーバーエラー |
| -503 | 読み込みタイムアウト |

## ベストプラクティス

### 1. エラーハンドリング
```python
def safe_jvread(jvlink, buffer_size=110000, max_retry=3):
    """エラーハンドリングを含むJVRead"""
    for attempt in range(max_retry):
        result = jvlink.JVRead(buffer_size, "")
        ret_code = result[0] if isinstance(result, tuple) else result
        
        if ret_code == -3:  # ダウンロード中
            time.sleep(1)
            continue
        elif ret_code == -503:  # タイムアウト
            time.sleep(5)
            continue
        else:
            return result
            
    raise Exception("Max retry exceeded")
```

### 2. データベース保存
```python
import sqlite3

def save_to_database(records, db_path="jravan.db"):
    """取得したデータをSQLiteに保存"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # テーブル作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS races (
            race_key TEXT PRIMARY KEY,
            race_date TEXT,
            course_code TEXT,
            race_number INTEGER,
            race_name TEXT,
            distance INTEGER,
            raw_data TEXT
        )
    """)
    
    # データ挿入
    for record in records:
        if record['type'] == 'RA':
            # レースデータの解析と保存
            data = record['data']
            values = (
                data[2:12],   # race_key
                data[12:20],  # race_date
                data[20:22],  # course_code
                int(data[22:24]),  # race_number
                data[24:84].strip(),  # race_name
                int(data[84:88]),  # distance
                data  # raw_data
            )
            
            cursor.execute("""
                INSERT OR REPLACE INTO races 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, values)
    
    conn.commit()
    conn.close()
```

### 3. 定期データ更新
```python
import schedule
import time

def update_data():
    """定期的なデータ更新処理"""
    reader = JVLinkReader()
    try:
        reader.initialize()
        # 差分データのみ取得
        reader.open_data("DIFF", "99999999999999", 1)
        records = reader.read_data(max_records=1000)
        save_to_database(records)
    finally:
        reader.close()

# 毎日午前5時に更新
schedule.every().day.at("05:00").do(update_data)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 4. メモリ効率的な処理
```python
def process_large_data(jvlink, batch_size=100):
    """大量データの効率的処理"""
    batch = []
    
    while True:
        result = jvlink.JVRead(110000, "")
        ret_code = result[0] if isinstance(result, tuple) else result
        
        if ret_code > 0:
            batch.append(result)
            
            if len(batch) >= batch_size:
                # バッチ処理
                process_batch(batch)
                batch.clear()
                
        elif ret_code == 0:
            # 残りのデータを処理
            if batch:
                process_batch(batch)
            break
```

## トラブルシューティング

### よくある問題と対策

#### 1. 「サービスキー認証エラー (-211)」
- **原因**: DataLabサービス未契約または認証失敗
- **対策**: JRA-VAN DataLabの契約確認、正しいSID使用

#### 2. 「32ビット/64ビット互換性問題」
- **原因**: 64ビットPythonから32ビットDLL呼び出し
- **対策**: 
  - 32ビットPython使用
  - DLLサロゲート設定
  - Docker等で32ビット環境構築

#### 3. 「文字化け」
- **原因**: 文字コード不一致（Shift-JIS）
- **対策**: 
```python
# Shift-JISデコード
decoded_text = data.encode('latin-1').decode('shift-jis', errors='ignore')
```

#### 4. 「ダウンロード待機が長い」
- **原因**: 大量データの初回ダウンロード
- **対策**: 
  - セットアップデータ（option=3）で必要最小限取得
  - JVStatusで進捗確認
  - 夜間等のオフピーク時間に実行

## パフォーマンス最適化

### 1. 並列処理
```python
from concurrent.futures import ThreadPoolExecutor
import threading

lock = threading.Lock()

def process_record(record):
    """レコード処理"""
    # 処理実装
    pass

def parallel_processing(records):
    """並列処理"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_record, records)
```

### 2. キャッシュ活用
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_horse_info(horse_id):
    """馬情報のキャッシュ"""
    # データベースから取得
    return horse_data
```

### 3. インデックス最適化
```sql
-- データベースインデックス作成
CREATE INDEX idx_race_date ON races(race_date);
CREATE INDEX idx_horse_id ON results(horse_id);
CREATE INDEX idx_jockey_id ON results(jockey_id);
```

## セキュリティ考慮事項

1. **認証情報の管理**
   - SIDを環境変数で管理
   - 設定ファイルはgitignoreに追加

2. **データアクセス制限**
   - 必要最小限のデータのみ取得
   - アクセスログの記録

3. **エラー情報の取り扱い**
   - エラーログに認証情報を含めない
   - 本番環境では詳細エラーを隠蔽

## まとめ

JRA-VAN DataLabのJV-Link APIは、日本の競馬データを取得するための最も信頼性の高い公式APIです。

### 主な特徴
- **公式データ**: JRA直営で最も正確なデータ
- **リアルタイム**: オッズ、馬体重等の速報データ
- **包括的**: レース、馬、騎手等の全データ
- **固定長形式**: 高速処理可能な構造化データ

### 実装のポイント
1. 32ビット制限への対応（Python/C#共通）
2. 適切なエラーハンドリング
3. 効率的なデータ解析とDB保存
4. 定期更新の自動化

### 推奨利用方法
- **初期導入**: セットアップデータで基本データ取得
- **日次更新**: 差分データで効率的更新
- **リアルタイム**: 速報系APIで最新情報取得

月額2,090円の投資で、高品質な競馬データに基づく予測モデル開発が可能になります。

## 参考資料

- [JRA-VAN公式サイト](https://jra-van.jp/)
- [JRA-VAN DataLab SDK](https://jra-van.jp/dlb/sdv/sdk.html)
- [開発者コミュニティ](https://developer.jra-van.jp/)
- [pywin32ドキュメント](https://github.com/mhammond/pywin32)

---
*最終更新日: 2025年8月28日*