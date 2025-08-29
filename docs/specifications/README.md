# JRA-VAN 技術仕様書

## 概要

本ディレクトリには、JRA-VAN Data Lab.システムの技術仕様書を格納する。  
Version 4.9.0.2に準拠した完全な技術リファレンスである。

## 仕様書一覧

### 1. [データ構造仕様書](DATA_STRUCTURE_SPECIFICATION.md)
- レコード構造体定義
- データ型定義
- データ識別体系
- フィールド詳細仕様

### 2. [コードマスタ仕様書](CODE_MASTER_SPECIFICATION.md)
- 競馬場コード
- グレードコード
- 性別・毛色コード
- 馬記号コード
- 異常区分コード
- 天候・馬場状態コード
- その他各種コード定義

### 3. [データ種別仕様書](DATA_TYPE_SPECIFICATION.md)
- 蓄積系データ仕様
- 速報系データ仕様
- データ取得パラメータ
- データサイズ目安

### 4. [通信プロトコル仕様書](COMMUNICATION_PROTOCOL_SPECIFICATION.md)
- JVLink COMインターフェース
- 通信シーケンス
- データ通信仕様
- セッション管理
- 認証仕様
- パフォーマンス仕様

### 5. [データ更新仕様書](DATA_UPDATE_SPECIFICATION.md)
- 更新タイムテーブル
- データ更新ルール
- 差分更新仕様
- エラー処理
- 特殊更新パターン

## 関連ドキュメント

### 上位ドキュメント
- [JRA-VAN データ仕様書](../JRA-VAN_DATA_SPECIFICATION.md) - 概要説明
- [レコードフォーマット詳細](../RECORD_FORMAT_DETAILS.md) - 詳細実装仕様

### API設計
- [REST API設計書](../api-design/REST_API_DESIGN.md) - REST APIインターフェース設計

### 構造体定義
- [構造体仕様](../jra-van-specs/structures/) - 各構造体の詳細定義

## バージョン情報

| 項目 | 内容 |
|------|------|
| SDK Version | 4.9.0.2 |
| 文書更新日 | 2025年8月29日 |
| 対応OS | Windows 10/11 (32-bit) |
| 必須環境 | .NET Framework 4.8 |

## 参照規格

- JRA-VAN Data Lab. SDK仕様
- COM/OLE Automation規格
- HTTP/1.1 (RFC 7230-7235)
- Shift-JIS (CP932)

## 注意事項

1. **アーキテクチャ制限**: JVLink COMコンポーネントは32ビット専用
2. **文字コード**: すべてのデータはShift-JIS（CP932）エンコーディング
3. **同時接続**: 1セッションのみ許可
4. **データ形式**: 固定長テキスト形式

## ライセンス

本仕様書はJRA-VAN Data Lab.の公式仕様に基づく。  
データ利用にはJRAとの契約が必要。

---

*JRA-VAN Data Lab. Technical Specifications*  
*Version 4.9.0.2*