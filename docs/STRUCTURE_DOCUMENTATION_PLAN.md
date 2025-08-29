# 構造体ドキュメント統合計画

## 現状分析

### 1. 正式ドキュメントに記載済みの構造体
`docs/specifications/DATA_STRUCTURE_SPECIFICATION.md`に記載：

- RA - レース詳細 (409バイト)
- SE - 馬毎レース情報 (555バイト)
- HR - 払戻情報 (可変長)
- O1 - 単勝・複勝オッズ (1816バイト)
- WH - 馬体重 (351バイト)
- WE - 天候・馬場状態変更 (141バイト)
- UM - 競走馬マスタ (1889バイト)
- KS - 騎手マスタ (3863バイト)

### 2. structures内のMDファイル（56個）

#### 基本データ型（正式ドキュメント未記載）
- ymd.md - 年月日
- hms.md - 時分秒
- hm.md - 時分
- mdhm.md - 月日時分

#### 識別子型（一部記載済み）
- record_id.md - レコード識別 ❌
- race_id.md - レース識別（レースID構成として記載済み）✅
- race_id2.md - レース識別拡張 ❌

#### レース情報（未記載）
- race_info.md ❌
- race_jyoken.md ❌
- corner_info.md ❌
- tenko_baba_info.md ❌
- tokuuma_info.md ❌

#### 成績情報（未記載）
- chakukaisu3_info.md～chakukaisu6_info.md (4個) ❌
- chakuuma_info.md ❌
- sei_ruikei_info.md ❌
- saikin_jyusyo_info.md ❌
- hon_zen_ruikeisei_info.md ❌
- recuma_info.md ❌

#### 払戻・票数（未記載）
- pay_info1.md～pay_info4.md (4個) ❌
- hyo_info1.md～hyo_info4.md (4個) ❌

#### オッズ（一部記載済み）
- odds_tansyo_info.md（O1の一部として記載）✅
- odds_fukusyo_info.md（O1の一部として記載）✅
- odds_wakuren_info.md ❌
- odds_umaren_info.md ❌
- odds_wide_info.md ❌
- odds_umatan_info.md ❌
- odds_sanren_info.md ❌
- odds_sanrentan_info.md ❌

#### 出走別着度数（未記載）
- jv_ck_uma.md ❌
- jv_ck_kisyu.md ❌
- jv_ck_chokyosi.md ❌
- jv_ck_banusi.md ❌
- jv_ck_breeder.md ❌
- jv_ck_hon_ruikeisei_info.md ❌

#### その他（未記載）
- bataijyu_info.md（WHの一部として記載）✅
- ketto3_info.md ❌
- hatukijyo_info.md ❌
- hatusyori_info.md ❌
- jyusyo_info.md ❌
- jc_info.md ❌
- tc_info.md ❌
- cc_info.md ❌
- dm_info.md ❌
- tm_info.md ❌
- wf_race_info.md ❌
- wf_yuko_hyo_info.md ❌
- wf_pay_info.md ❌

## 実行計画

### フェーズ1: 正式ドキュメントの拡充
1. DATA_STRUCTURE_SPECIFICATION.mdに未記載の構造体を追加
2. 小規模構造体は「サブ構造体」セクションとして追加
3. 大規模構造体は個別セクションとして追加

### フェーズ2: 削除対象の特定
以下は正式ドキュメントに含まれているため削除可能：
- race_id.md（レースID構成として記載済み）
- odds_tansyo_info.md（O1の一部）
- odds_fukusyo_info.md（O1の一部）
- bataijyu_info.md（WHの一部）

### フェーズ3: 追加が必要な構造体（48個）
正式ドキュメントに追加すべき構造体

#### 優先度高（基本構造体）
- YMD, HMS, HM, MDHM（日時型）
- RECORD_ID（レコード識別）
- RACE_INFO, RACE_JYOKEN（レース基本情報）

#### 優先度中（詳細情報）
- CHAKUKAISU系（着回数）
- PAY_INFO系（払戻）
- HYO_INFO系（票数）
- ODDS系（各種オッズ）
- JV_CK系（出走別着度数）

#### 優先度低（補助情報）
- 各種INFO系構造体

## 実装方針

1. **セクション構成の変更**
   - 現在の「2. レコード構造体定義」を「主要レコード構造体」に変更
   - 新セクション「7. サブ構造体定義」を追加
   - 新セクション「8. 出走別着度数構造体」を追加

2. **記載レベル**
   - 主要構造体：詳細なバイト位置まで記載
   - サブ構造体：フィールド名と型のみ記載

3. **削除基準**
   - 正式ドキュメントに完全に含まれている構造体MDは削除
   - 部分的に含まれている場合は、不足分を正式ドキュメントに追加後削除