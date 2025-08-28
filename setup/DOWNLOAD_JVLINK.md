# JV-Link.exe ダウンロード手順

## 重要：JV-Link.exeが必要です

JRA-VAN Clientを利用するためには、JRA-VAN公式サイトから`JV-Link.exe`をダウンロードして、このフォルダに配置する必要があります。

## ダウンロード手順

1. **JRA-VAN公式サイトにアクセス**
   - [https://jra-van.jp/dlb/#tab5](https://jra-van.jp/dlb/#tab5) を開く

2. **SDKをダウンロード**
   - 「ソフトウェア開発キット（SDK）」タブをクリック
   - 最新版の「JRA-VAN Data Lab. SDK」をダウンロード
   - ZIPファイルがダウンロードされます

3. **JV-Link.exeを抽出**
   - ダウンロードしたZIPファイルを解凍
   - `JV-Link\JV-Link.exe` を見つける

4. **このフォルダにコピー**
   - 抽出した`JV-Link.exe`を**このフォルダ（setup/）**にコピー
   - 正しいパス: `setup/JV-Link.exe`

## 確認方法

以下のコマンドでファイルが正しく配置されているか確認できます：

```bash
dir JV-Link.exe
```

ファイルが表示されれば準備完了です！

## 注意事項

- JV-Link.exeはJRA-VANの著作物のため、GitHubには含まれていません
- 必ず公式サイトから最新版をダウンロードしてください
- SDKのバージョンが更新された場合は、JV-Link.exeも更新してください

## トラブルシューティング

**Q: ダウンロードリンクが見つからない**  
A: JRA-VANの会員登録（無料）が必要な場合があります

**Q: どのバージョンをダウンロードすべき？**  
A: 最新版（現在はVer4.9.0.2以降）を推奨します

**Q: 32bit版と64bit版がある？**  
A: JV-Link.exeは32bitアプリですが、本クライアントは64bit環境でも動作します