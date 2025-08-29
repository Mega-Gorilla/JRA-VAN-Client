# JRA-VAN レコードフォーマット詳細仕様

## 目次

1. [レコード種別一覧](#レコード種別一覧)
2. [主要レコード詳細](#主要レコード詳細)
3. [データ型定義](#データ型定義)
4. [実装サンプル](#実装サンプル)

---

## レコード種別一覧

### 蓄積系データレコード

| レコード種別 | 説明 | サイズ（バイト） | データスペック |
|------------|------|-----------------|---------------|
| RA | レース詳細 | 409 | RACE, DIFF |
| SE | 馬毎レース情報 | 555 | RACE, DIFF |
| HR | 払戻 | 可変 | RACE, DIFF |
| H1 | 票数（単複枠） | 可変 | RACE, DIFF |
| H6 | 票数（3連単） | 可変 | RACE, DIFF |
| O1 | オッズ（単複枠） | 可変 | RACE, DIFF |
| O6 | オッズ（3連単） | 可変 | RACE, DIFF |
| UM | 競走馬マスタ | 1889 | HOSE |
| KS | 騎手マスタ | 3863 | KISI |
| CH | 調教師マスタ | 3509 | CYOS |
| BR | 生産者マスタ | 703 | BREU |
| BN | 馬主マスタ | 291 | OWNR |
| HN | 繁殖馬 | 2591 | BLOD |
| SK | 産駒馬 | 743 | BLOD |
| RC | レコード | 113 | WOOD |
| HC | 調教本追切 | 203 | SLOP |
| YS | 年間スケジュール | 263 | YSCH |
| CS | コース | 63 | COSE |
| CC | 競走馬市場取引価格 | 203 | HOSE |
| DM | データマイニング | 573 | MING |
| TM | タイム型データマイニング | 673 | MING |

### 速報系データレコード

| レコード種別 | 説明 | サイズ（バイト） | データスペック |
|------------|------|-----------------|---------------|
| WH | 馬体重 | 351 | 0B11 |
| WE | 天候・馬場状態変更 | 141 | 0B12 |
| WC | 出走取消・競走除外 | 67 | 0B13 |
| AV | 騎手変更 | 87 | 0B14 |
| JC | 発走時刻変更 | 23 | 0B15 |
| TC | 登録頭数 | 213 | 0B16 |
| CC | コース変更 | 61 | 0B17 |
| WF | WIN5 | 351/463 | 0B31 |

---

## 主要レコード詳細

### RA - レース詳細（409バイト）

レースの基本情報を格納する最も重要なレコード。

```
位置  長さ  項目名                    型        説明
----  ----  ----------------------  --------  --------------------------
1     2     レコード種別              X(2)      "RA"固定
3     16    レースキー情報
  3   4     └開催年                  9(4)      西暦4桁
  7   4     └開催月日                9(4)      MMDD形式
  11  2     └競馬場コード            X(2)      01:札幌～10:小倉
  13  2     └開催回[第N回]           X(2)      01～09
  15  2     └開催日目[N日目]         X(2)      01～12
  17  2     └レース番号              X(2)      01～12

19    1     曜日コード                X(1)      1:日～7:土
20    4     特別競走番号              9(4)      0000:特別競走以外
24    60    競走名本題                X(60)     全角30文字
84    60    競走名副題                X(60)     全角30文字
144   36    競走名カッコ内            X(36)     全角18文字
180   120   競走名本題欧字            X(120)    半角120文字
300   120   競走名副題欧字            X(120)    半角120文字
420   36    競走名カッコ内欧字        X(36)     半角36文字

456   20    競走名略称10文字          X(20)     全角10文字
476   12    競走名略称6文字           X(12)     全角6文字
488   6     競走名略称3文字           X(6)      全角3文字
494   1     競走名区分                X(1)      0:通常 1:重賞
495   2     重賞回次[第N回]           X(2)      00:非重賞

497   1     グレードコード            X(1)      A:G1 B:G2 C:G3...
498   1     グレード年次              X(1)      変更前のグレード
499   50    競走条件本題              X(50)     "3歳以上"等
549   50    競走条件副題              X(50)     
599   30    競走条件カッコ内          X(30)     
629   3     競走条件コード            X(3)      
  629 1     └競走種別                X(1)      1:平地 2:障害
  630 1     └競走記号                X(1)      1:指定 2:特指 3:若手
  631 1     └重量種別                X(1)      1:ハンデ 2:別定 3:馬齢 4:定量

632   5     競走条件コード            X(5)      
  632 1     └2歳条件                 X(1)      0:無関係 1:対象
  633 1     └3歳条件                 X(1)      0:無関係 1:対象
  634 1     └4歳条件                 X(1)      0:無関係 1:対象
  635 1     └5歳以上条件             X(1)      0:無関係 1:対象
  636 1     └最若年条件              X(1)      0:無関係 1:対象

637   4     距離                      9(4)      メートル単位
641   1     トラックコード            X(1)      1:芝 2:ダート 3:障害芝 4:障害ダート
642   8     本賞金                    
  642 5     └1着                     9(5)      万円単位（0:未定）
  647 3     └2着                     9(3)      万円単位（0:未定）
  650 3     └3着                     9(3)      万円単位（0:未定）
  653 3     └4着                     9(3)      万円単位（0:未定）
  656 3     └5着                     9(3)      万円単位（0:未定）
  
659   8     付加賞金                  
  659 5     └1着                     9(5)      万円単位（0:未定）
  664 3     └2着                     9(3)      万円単位（0:未定）
  667 3     └3着                     9(3)      万円単位（0:未定）
  
670   5     発走時刻                  X(5)      HH:MM形式
675   2     登録頭数                  99        
677   2     出走頭数                  99        
679   1     天候コード                X(1)      1:晴 2:曇 3:雨 4:小雨 5:雪 6:小雪
680   2     芝馬場状態コード          X(2)      10:良 11:稍重 12:重 13:不良
682   2     ダート馬場状態コード      X(2)      20:良 21:稍重 22:重 23:不良

684   5     ラップタイム              
  684 1     └ラップ数                99        
  685 120   └各ラップ                S9(3)×40  1/10秒単位

805   5     ペース                    
  805 3     └前半                    S9(3)     1/10秒単位
  808 3     └後半                    S9(3)     1/10秒単位

811   2     改行                      X(2)      CR+LF
```

### SE - 馬毎レース情報（555バイト）

出走馬ごとのレース結果詳細。

```
位置  長さ  項目名                    型        説明
----  ----  ----------------------  --------  --------------------------
1     2     レコード種別              X(2)      "SE"固定
3     16    レースキー情報            X(16)     RAレコードと同一
19    2     馬番                      X(2)      01～28（00:取消）
21    10    血統登録番号              X(10)     YYYY+6桁番号
31    36    馬名                      X(36)     全角18文字
67    1     性別コード                X(1)      1:牡 2:牝 3:セン
68    1     調教師区分                X(1)      1:美浦 2:栗東
69    5     調教師コード              X(5)      
74    36    調教師名                  X(36)     全角18文字
110   1     馬主コード                X(6)      
116   64    馬主名                    X(64)     全角32文字
180   1     市場取引フラグ            X(1)      0:なし 1:あり
181   60    父馬名                    X(60)     全角30文字
241   60    母馬名                    X(60)     全角30文字
301   60    母父馬名                  X(60)     全角30文字
361   2     馬齢                      99        
363   3     負担重量                  999       0.1kg単位（570=57.0kg）
366   1     ブリンカー使用区分        X(1)      0:なし 1:あり
367   1     騎手見習区分              X(1)      0:なし 1:あり（☆△▲）
368   5     騎手コード                X(5)      
373   16    騎手名                    X(16)     全角8文字
389   3     負担重量差                S99       増減kg（+1/-2等）
392   1     異常区分                  X(1)      1:取消 2:除外 3:中止 4:失格
393   2     着順                      99        00:着外/異常
395   4     走破タイム                9(4)      1/10秒単位（1234=2分03秒4）
399   3     着差                      999       1/10秒単位
402   3     単勝人気順位              999       
405   7     単勝オッズ                9999.9    
412   1     ペース                    X(1)      H:ハイ M:ミドル S:スロー
413   1     上がりタイム区分          X(1)      1:上がり最速
414   5     上がり3ハロンタイム       999.9     1/10秒単位
419   20    コーナー通過順位          
  419 5     └1コーナー               99-99     順位範囲
  424 5     └2コーナー               99-99     
  429 5     └3コーナー               99-99     
  434 5     └4コーナー               99-99     
439   3     前走着順                  999       
442   5     前走人気                  999       
447   16    前走レースキー            X(16)     
463   36    前走レース名              X(36)     全角18文字
499   2     前走頭数                  99        
501   1     前走異常区分              X(1)      
502   3     タイム差                  S99       1/10秒単位（±）
505   2     馬体重                    999       kg単位
507   3     馬体重増減                S99       kg単位（+10/-5等）
510   44    予備                      X(44)     将来拡張用
554   2     改行                      X(2)      CR+LF
```

### O1 - 単勝・複勝オッズ（1785バイト）

リアルタイムオッズ情報。

```
位置  長さ  項目名                    型        説明
----  ----  ----------------------  --------  --------------------------
1     2     レコード種別              X(2)      "O1"固定
3     16    レースキー情報            X(16)     
19    8     発表日時                  
  19  4     └年月日                  9(4)      MMDD
  23  4     └時分                    9(4)      HHMM
27    3     登録頭数                  999       
30    3     出走頭数                  999       
33    1     発売フラグ                
  33  1     └単勝                    X(1)      0:発売なし 1:発売あり 7:発売前
  34  1     └複勝                    X(1)      0:発売なし 1:発売あり 7:発売前
  35  1     └枠連                    X(1)      0:発売なし 1:発売あり 7:発売前
36    1590  単勝オッズ                
  36  30     └馬番01                  
    36 1    　└取消フラグ            X(1)      1:取消/除外 0:通常
    37 29   　└オッズ情報            
      37 10   └合計票数              9(10)     票数
      47 6    └オッズ               9999.9    10.5倍等
      53 3    └人気順               999       
  66  30     └馬番02                  
  ...
  906 30     └馬番28                  
936   850   複勝オッズ                
  936 30     └馬番01                  
    936 1   　└取消フラグ            X(1)      
    937 29  　└オッズ情報            
      937 10  └合計票数              9(10)     
      947 6   └最低オッズ            9999.9    
      953 3   └最低人気              999       
      956 6   └最高オッズ            9999.9    
      962 3   └最高人気              999       
  966 30     └馬番02                  
  ...
1786  850   └馬番28                  
1816  2     改行                      X(2)      CR+LF
```

### WH - 馬体重（351バイト）

発走前の馬体重情報。

```
位置  長さ  項目名                    型        説明
----  ----  ----------------------  --------  --------------------------
1     2     レコード種別              X(2)      "WH"固定
3     16    レースキー情報            X(16)     
19    8     発表日時                  
  19  4     └月日                    9(4)      MMDD
  23  4     └時分                    9(4)      HHMM
27    324   馬体重情報                
  27  12    └馬番01                  
    27 1    　└取消フラグ            X(1)      1:取消/除外
    28 3    　└馬体重               999       kg単位（0:計不）
    31 3    　└増減                 S99       前走比（+10/-5等）
    34 5    　└予備                 X(5)      
  39  12    └馬番02                  
  ...
  339 12    └馬番28                  
351   2     改行                      X(2)      CR+LF
```

---

## データ型定義

### 基本データ型

| 記号 | 型名 | サイズ | 説明 | 例 |
|-----|------|--------|------|-----|
| 9 | 数値 | 可変 | 右詰めゼロパディング | "0123" |
| X | 文字 | 可変 | 左詰めスペースパディング | "ABC " |
| S9 | 符号付き数値 | 可変 | 先頭1バイトが符号 | "+123", "-045" |
| N | 全角文字 | 可変×2 | 全角1文字=2バイト | "ウマ" |

### 複合データ型

#### 日付型（YYYYMMDD）
```
位置  長さ  内容
1     4     年（西暦）
5     2     月（01-12）
7     2     日（01-31）
```

#### 時刻型（HHMMSS）
```
位置  長さ  内容
1     2     時（00-23）
3     2     分（00-59）
5     2     秒（00-59）
```

#### タイム型（MMSS.F）
```
位置  長さ  内容
1     1     分（0-9）
2     2     秒（00-59）
4     1     小数点
5     1     1/10秒（0-9）
```

---

## 実装サンプル

### Python実装例

#### レコードパーサー基底クラス

```python
from dataclasses import dataclass
from typing import Optional, List
import struct

class RecordParser:
    """JRA-VANレコードパーサー基底クラス"""
    
    def __init__(self, data: bytes):
        self.data = data
        self.position = 0
    
    def read_string(self, length: int) -> str:
        """固定長文字列を読み取り"""
        value = self.data[self.position:self.position + length]
        self.position += length
        return value.decode('cp932').strip()
    
    def read_number(self, length: int) -> int:
        """固定長数値を読み取り"""
        value = self.data[self.position:self.position + length]
        self.position += length
        try:
            return int(value)
        except ValueError:
            return 0
    
    def read_signed_number(self, length: int) -> int:
        """符号付き数値を読み取り"""
        sign_byte = self.data[self.position:self.position + 1]
        number_bytes = self.data[self.position + 1:self.position + length]
        self.position += length
        
        sign = 1 if sign_byte == b'+' else -1
        try:
            return sign * int(number_bytes)
        except ValueError:
            return 0
```

#### RAレコードパーサー

```python
@dataclass
class RaceHeader:
    """RAレコード（レース詳細）"""
    record_type: str
    year: str
    month_day: str
    jyo_cd: str
    kaiji: str
    nichiji: str
    race_num: str
    youbi_cd: str
    toku_num: str
    hondai: str
    fukudai: str
    kakko: str
    hondai_eng: str
    fukudai_eng: str
    kakko_eng: str
    ryakusyo10: str
    ryakusyo6: str
    ryakusyo3: str
    kubun: str
    nkai: str
    grade_cd: str
    grade_before: str
    jyoken_hondai: str
    jyoken_fukudai: str
    jyoken_kakko: str
    syubetsu_cd: str
    kigo_cd: str
    jyuryo_cd: str
    jyoken_cd: str
    kyori: int
    track_cd: str
    honsyokin: List[int]
    fukasyokin: List[int]
    hassotime: str
    toroku_tosu: int
    syusso_tosu: int
    tenko_cd: str
    shiba_baba_cd: str
    dirt_baba_cd: str
    lap_time: List[int]
    pace_mae: int
    pace_ato: int
    
    @classmethod
    def parse(cls, data: bytes) -> 'RaceHeader':
        """バイトデータからRAレコードをパース"""
        parser = RecordParser(data)
        
        # レコード種別
        record_type = parser.read_string(2)
        if record_type != "RA":
            raise ValueError(f"Invalid record type: {record_type}")
        
        # レースキー情報
        year = parser.read_string(4)
        month_day = parser.read_string(4)
        jyo_cd = parser.read_string(2)
        kaiji = parser.read_string(2)
        nichiji = parser.read_string(2)
        race_num = parser.read_string(2)
        
        # レース情報
        youbi_cd = parser.read_string(1)
        toku_num = parser.read_string(4)
        hondai = parser.read_string(60)
        fukudai = parser.read_string(60)
        kakko = parser.read_string(36)
        hondai_eng = parser.read_string(120)
        fukudai_eng = parser.read_string(120)
        kakko_eng = parser.read_string(36)
        ryakusyo10 = parser.read_string(20)
        ryakusyo6 = parser.read_string(12)
        ryakusyo3 = parser.read_string(6)
        kubun = parser.read_string(1)
        nkai = parser.read_string(2)
        
        # グレード・条件
        grade_cd = parser.read_string(1)
        grade_before = parser.read_string(1)
        jyoken_hondai = parser.read_string(50)
        jyoken_fukudai = parser.read_string(50)
        jyoken_kakko = parser.read_string(30)
        
        # 競走条件コード
        syubetsu_cd = parser.read_string(1)
        kigo_cd = parser.read_string(1)
        jyuryo_cd = parser.read_string(1)
        jyoken_cd = parser.read_string(5)
        
        # 距離・コース
        kyori = parser.read_number(4)
        track_cd = parser.read_string(1)
        
        # 本賞金
        honsyokin = [
            parser.read_number(5),
            parser.read_number(3),
            parser.read_number(3),
            parser.read_number(3),
            parser.read_number(3)
        ]
        
        # 付加賞金
        fukasyokin = [
            parser.read_number(5),
            parser.read_number(3),
            parser.read_number(3)
        ]
        
        # その他情報
        hassotime = parser.read_string(5)
        toroku_tosu = parser.read_number(2)
        syusso_tosu = parser.read_number(2)
        tenko_cd = parser.read_string(1)
        shiba_baba_cd = parser.read_string(2)
        dirt_baba_cd = parser.read_string(2)
        
        # ラップタイム
        lap_count = parser.read_number(1)
        lap_time = []
        for _ in range(lap_count):
            lap_time.append(parser.read_signed_number(3))
        
        # ペース
        pace_mae = parser.read_signed_number(3)
        pace_ato = parser.read_signed_number(3)
        
        return cls(
            record_type=record_type,
            year=year,
            month_day=month_day,
            jyo_cd=jyo_cd,
            kaiji=kaiji,
            nichiji=nichiji,
            race_num=race_num,
            youbi_cd=youbi_cd,
            toku_num=toku_num,
            hondai=hondai,
            fukudai=fukudai,
            kakko=kakko,
            hondai_eng=hondai_eng,
            fukudai_eng=fukudai_eng,
            kakko_eng=kakko_eng,
            ryakusyo10=ryakusyo10,
            ryakusyo6=ryakusyo6,
            ryakusyo3=ryakusyo3,
            kubun=kubun,
            nkai=nkai,
            grade_cd=grade_cd,
            grade_before=grade_before,
            jyoken_hondai=jyoken_hondai,
            jyoken_fukudai=jyoken_fukudai,
            jyoken_kakko=jyoken_kakko,
            syubetsu_cd=syubetsu_cd,
            kigo_cd=kigo_cd,
            jyuryo_cd=jyuryo_cd,
            jyoken_cd=jyoken_cd,
            kyori=kyori,
            track_cd=track_cd,
            honsyokin=honsyokin,
            fukasyokin=fukasyokin,
            hassotime=hassotime,
            toroku_tosu=toroku_tosu,
            syusso_tosu=syusso_tosu,
            tenko_cd=tenko_cd,
            shiba_baba_cd=shiba_baba_cd,
            dirt_baba_cd=dirt_baba_cd,
            lap_time=lap_time,
            pace_mae=pace_mae,
            pace_ato=pace_ato
        )
```

#### 使用例

```python
def process_jvdata(file_path: str):
    """JVデータファイルを処理"""
    
    with open(file_path, 'rb') as f:
        while True:
            # レコード種別を確認
            record_type = f.read(2)
            if not record_type:
                break
            
            f.seek(-2, 1)  # 2バイト戻る
            
            # レコード種別に応じて処理
            if record_type == b'RA':
                # RAレコードを読み込み
                data = f.read(409)
                race = RaceHeader.parse(data)
                print(f"レース: {race.hondai}")
                
            elif record_type == b'SE':
                # SEレコードを読み込み
                data = f.read(555)
                # 処理...
                
            else:
                # 不明なレコード、1行読み飛ばし
                f.readline()
```

### C#実装例

```csharp
using System;
using System.Text;
using System.Runtime.InteropServices;

[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
public struct JV_RA_RACE
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 2)]
    public string RecordSpec;    // レコード種別
    
    public RACE_ID id;           // レースID
    public RACE_INFO RaceInfo;   // レース情報
    public RACE_JYOKEN JyokenInfo; // 条件情報
    
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 4)]
    public string Kyori;         // 距離
    
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 1)]
    public string TrackCD;       // トラックコード
    
    // 本賞金
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 5)]
    public HONSYOKIN_INFO[] Honsyokin;
    
    // 付加賞金
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 3)]
    public FUKASYOKIN_INFO[] Fukasyokin;
    
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 5)]
    public string HassoTime;     // 発走時刻
    
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 2)]
    public string TorokuTosu;    // 登録頭数
    
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 2)]
    public string SyussoTosu;    // 出走頭数
    
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 1)]
    public string TenkoCD;       // 天候コード
    
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 2)]
    public string ShibaBabaCD;   // 芝馬場状態
    
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 2)]
    public string DirtBabaCD;    // ダート馬場状態
    
    public LAP_TIME LapTime;     // ラップタイム
    public PACE_INFO Pace;       // ペース
    
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 2)]
    public string crlf;          // 改行
}

// 使用例
public class JVDataProcessor
{
    public void ProcessRaceData(byte[] data)
    {
        // バイト配列を構造体に変換
        GCHandle handle = GCHandle.Alloc(data, GCHandleType.Pinned);
        try
        {
            JV_RA_RACE race = (JV_RA_RACE)Marshal.PtrToStructure(
                handle.AddrOfPinnedObject(), 
                typeof(JV_RA_RACE)
            );
            
            Console.WriteLine($"レース: {race.RaceInfo.Hondai}");
            Console.WriteLine($"距離: {race.Kyori}m");
            Console.WriteLine($"発走時刻: {race.HassoTime}");
        }
        finally
        {
            handle.Free();
        }
    }
}
```

---

## 参考資料

- [JRA-VAN公式サイト](https://jra-van.jp/)
- [JVLink SDK](https://jra-van.jp/dlb/sdv/sdk.html)
- [データ仕様書PDF](https://jra-van.jp/dlb/sdv/doc/JV-Data_Spec.pdf)

---

*最終更新: 2025年8月29日*
*バージョン: 4.9.0.2*