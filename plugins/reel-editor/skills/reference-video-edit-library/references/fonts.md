# パターン別の文字を別の環境で再現する

## A02の書体について

A02の0.4.2以降は、利用者が完成承認した制作字体を既定にする。前半の太字はHiraginoSans-W8、明朝はHiraMinProN-W6。いずれも元見本の書体名を同定したものではなく、実映像との比較で選び、完成版として承認された近似である。終盤の白はHiraginoSans-W7、オレンジはHiraginoSans-W8で、こちらは元編集データで特定済み。`a02.json`のcue.postscriptNameとfontIdentityを一緒に確認する。

承認版を使う依頼ではこの字体選定を再び未決事項にしない。利用可能な正しい字体を確認して進める。必要なフォントが無い場合は不足を知らせ、黙ってNotoなどへ変えない。macOSのTTCはファイル名や順番だけで判断せず、PostScript名が一致するfaceを選ぶ。フォント本体や汎用字形辞書は共有物へ含めず、その案件で必要な文字だけを用意する。

原見本の前半の字体は引き続き未特定。`a02-reference.json`は原観測の記録であり、承認版の配置・色・縁・動きを上書きする既定ではない。各案件で太さ・行幅・影・実背景上の読みやすさを合成確認し、全編が元見本と同一フォントという報告をしない。

## A01の同定済み書体

元原稿から特定した本文は **VDL Ｖ７明朝 U（PostScript名 VDL-V7Mincho-Ultra）**、冒頭は **ふい字P v2.9（HuiFontP）**。Notoは同じフォントではない。厳密なA01では、利用者が持つ元フォントとその利用方法を確認してから文字を組む。元フォントが使えない場合も映像と台本は進められるが、字体の高再現は未準備とする。

利用可能なフォントについて、全文の字形を抽出してSVG表示にする経路を用意している。CapCutキャッシュにファイルがあるだけで、他アプリでの利用やアウトライン変換・埋め込み・再配布が許可されるとは判断しない。管理者のキャッシュファイルや、任意の文章を描ける汎用字形辞書を共有物へ入れない。利用権に合うフォントファイルが各利用者に用意できた場合だけこの経路を使う。

同梱Notoは、利用者が明示的に近似を選んだ場合の代替とテスト用。ファイル不足を理由に自動でNotoへ変えない。

## フォントと配布条件

元フォント同定日：2026-10-05。Noto・ふい字Pの同梱条件確認日：2026-09-25。

| 用途 | フォント | プラグインに同梱 | 根拠・扱い |
| --- | --- | --- | --- |
| 本文の元フォント | VDL Ｖ７明朝 U / VDL-V7Mincho-Ultra | しない | 原稿・name table一致。キャッシュ由来ファイルの外部利用・再配布許諾は未確認。利用者が正当に使えるファイルと条件を確認。 |
| 承諾された本文の近似 | Noto Serif CJK JP Black v2.003 | する | 公式 SIL Open Font License 1.1。未改変OTF、著作権表示、ライセンス全文を一緒に保存。 |
| 冒頭 | ふい字P v2.9 / HuiFontP29.ttf | しない | 作者Readmeは個人・商用の使用を認める一方、本体の販売・加工を禁止し、再配布・掲載には事前の連絡を求めている。今回はその連絡を行っていない。 |

Notoの一次資料：

- [公式リポジトリ](https://github.com/notofonts/noto-cjk)
- [公式 v2.003 の日本語 Black OTF](https://raw.githubusercontent.com/notofonts/noto-cjk/Serif2.003/Serif/OTF/Japanese/NotoSerifCJKjp-Black.otf)
- [公式 Serif ライセンス全文](https://raw.githubusercontent.com/notofonts/noto-cjk/main/Serif/LICENSE)
- [Noto公式の利用・同梱説明](https://notofonts.github.io/noto-docs/website/use/)

同梱先は `assets/fonts/NotoSerifCJKjp-Black.otf`。OFLは `assets/fonts/NotoSerifCJK-LICENSE.txt`、フォント自身の著作権表示とハッシュは `assets/fonts/NotoSerifCJK-NOTICE.txt` に保存している。OTFは公式v2.003とSHA-256が一致する未改変ファイル。フォントだけの販売は禁止。フォントを再配布する場合は、著作権表示とOFL全文を保ち、他のライセンスへ変更しない。

ふい字Pの一次資料は、作者「ふい」が登録した [Vectorの配布ページ](https://www.vector.co.jp/soft/data/writing/se347444.html) から取得できる `HuiFontP29.lzh` 内の `HuiFontP29/Readme.txt`。「再配布・掲載については事前にお知らせください。」と明記されている。旧作者サイトの内容を今回取得できなかったため、現存する作者配布アーカイブのReadmeを確認した。フリーウェアという表示だけを再配布許可とは解釈しない。

## ふい字Pを初回取得する

Codexは最初に利用者の既存フォント保存先を確認し、まだ持っていない場合はその利用者のために配布元の確認・取得・展開を行う。利用者へ毎回ファイル操作を依頼しない。取得先は共有プラグインの外にある利用者の個人フォント保存先とし、2回目以降は保存したTTFを再利用する。

1. [Vectorのふい字Pダウンロードページ](https://www.vector.co.jp/soft/dl/data/writing/se347444.html) を開き、作者「ふい」、バージョン2.9、ファイル名 `HuiFontP29.lzh` を確認する。等幅版の「ふい字」とは別ファイル。
2. [配布のダウンロード画面](https://www.vector.co.jp/download/file/data/writing/fh435524.html) にあるリンクから取得する。確認時の作者配布アーカイブは [HuiFontP29.lzh](https://ftp.vector.co.jp/43/55/114/HuiFontP29.lzh)、LZH形式、2,467,519 bytes。
3. LZH対応の展開機能で開き、`HuiFontP29/HuiFontP29.ttf` と `HuiFontP29/Readme.txt` を同じ利用者管理フォルダへ保持する。利用条件は同梱Readmeで確認する。原フォント本体は改変しない。
4. 抽出CLIの `--font` に、その利用者の `HuiFontP29.ttf` のパスを渡す。OSへのフォントインストールは不要。

macOS標準の`tar`によるLZHの一覧確認・Readmeの展開を検証済み。Codexが使える実行例（`/path/to/user-fonts`は利用者の個人保存先へ置き換える）：

```sh
mkdir -p /path/to/user-fonts
curl --fail --location --max-time 60 https://ftp.vector.co.jp/43/55/114/HuiFontP29.lzh --output /path/to/user-fonts/HuiFontP29.lzh
tar -tf /path/to/user-fonts/HuiFontP29.lzh
tar -xf /path/to/user-fonts/HuiFontP29.lzh -C /path/to/user-fonts
```

一覧が上記のフォントとReadmeであることを確認してから展開する。ReadmeはShift_JISなので必要に応じてその文字コードで読む。環境の`tar`がLZH非対応なら、利用可能なLZH対応展開機能を使う。自動取得機能はCLIには組み込んでいない。

取得先が利用できない場合は、ふい字Pが未取得であることを伝えて冒頭文字の再現を保留する。代替フォントを使う場合は利用者の選択を受ける。ふい字P本体や抽出済みの汎用文字辞書をプラグインに追加しない。必要なプロジェクトの文字だけを各利用者の環境で抽出する。

## 文字の抽出

Python 3.9以上と `fontTools` が必要。Codexが作業用の仮想環境を用意し、そのPythonにだけ依存関係を入れる。環境は再利用し、利用者へ毎回のコマンド入力を求めない。依存ライブラリはプラグインへ同梱していない。以下はスキルのディレクトリから実行するmacOS/Linuxの例。

```sh
python3 -m venv /path/to/work/.glyph-venv
/path/to/work/.glyph-venv/bin/python -m pip install -r scripts/requirements.txt
/path/to/work/.glyph-venv/bin/python scripts/glyphs.py --font /path/to/user-licensed-font.ttf --expected-postscript-name VDL-V7Mincho-Ultra --text /path/to/body.txt --output /path/to/body-glyphs.json
/path/to/work/.glyph-venv/bin/python scripts/glyphs.py --font /path/to/HuiFontP29.ttf --expected-postscript-name HuiFontP --text /path/to/intro.txt --compact --output /path/to/intro-glyphs.json
```

`/path/to/...` はその利用者の作業場所と入力・出力パスに置き換える。仮想環境を共有プラグインには入れない。Windowsの仮想環境では`bin/python`の代わりに`Scripts/python.exe`を使う。入力文字列はUTF-8ファイルで渡す。改行・先頭末尾の空白・繰り返し文字を保持する。先頭のUTF-8 BOMを除き、CRLFとCRはLFへ統一する。タブは自動展開しない。タブが必要なら入力側で意図する数の半角空白へ変える。

TTC/OTCの場合は `--font-number 0` のように0起点のフォント番号を指定する。可変フォントはデフォルト軸値で抽出される。一般的な日本語横書き・英数字の文字単位の配置を対象としており、カーニング、合字、複雑な文字形成、縦書き、異体字セレクタの適用は行わない。`cmap`にないコードポイントは黙って代替しない。そうした処理が必要な文章は、このCLIでそのまま再現できるとは扱わない。

未収録文字がある場合は全件を `U+XXXX` と文字名で標準エラーに表示して終了コード3を返す。JSONは出力せず、既存出力ファイルも保持する。ファイル・UTF-8・フォント形式・依存関係のエラーは終了コード2。成功は0。`--output` を省略するとJSONを標準出力に出す。

## JSONの仕様

```json
{
  "schemaVersion": 1,
  "fontIdentity": {"postscriptName": "example", "family": "example", "fullName": "example"},
  "upem": 1000,
  "pathEncoding": "svg",
  "text": "院名\n本文 123",
  "glyphs": {
    " ": { "d": "", "a": 256, "b": null }
  }
}
```

上記は形を示す例で、空白の幅も実行時に実際のフォントから得る。`glyphs` には入力に含まれる文字が初出順に1回ずつ入る。改行は `text` に保持され、グリフにはならない。

- `fontIdentity`: 抽出したフォントの実名。`--expected-postscript-name`と一致しなければエラー終了する。
- `upem`: 1 emあたりのフォント内部単位数。
- `d`: SVGパス文字列。`pathEncoding` が `base36-int-v1` の場合は次節の復元が必要。
- `a`: 横方向の送り幅。描画のない空白も、この幅だけ次の文字位置を進める。
- `b`: 実際の輪郭の `[xMin, yMin, xMax, yMax]`。輪郭のない空白などは `null`。

座標はフォント座標のままで、ベースラインを `y=0`、上方向を正とする。サイズ `fontSize` なら `scale=fontSize/upem` を使い、SVGの各グリフに `translate(penX, baselineY) scale(scale, -scale)` を適用する。Notoの`upem`は1000、ふい字Pは1024なので、固定値を使わずJSONから読む。次の文字へは `a*scale`（必要なら指定の字間も）進める。LFで次の行の原点へ移動する。見た目を中央揃えするときは空白も含む送り幅と、輪郭の `b` のどちらを基準にするか意図を決める。

## compactの符号化と復元

`--compact` はJSONの余白を削り、`d`の数値を最も近い整数へ丸める。ちょうど0.5は0から遠い側へ丸める（`35.5→36`、`-35.5→-36`）。送り幅`a`、輪郭範囲`b`、`upem`は元の数値のまま。輪郭には最大0.5フォント単位の座標誤差が生じる。

パス命令は大文字 `M L H V Q C Z`、数値は小文字base36（`0-9a-z`）、負数は先頭`-`、同じ命令の数値は`,`で区切る。例：SVGの `M36 -36L100 0Z` は `M10,-10L2s,0Z`。命令の大文字と数値の小文字を区別するため、大文字・小文字を変更しない。

復元関数（JavaScript。これはフォントデータの復号例であり、JSXファイルとして保存しない）：

```js
const decodePath = (d, encoding) => {
  if (encoding === "svg") return d;
  if (encoding !== "base36-int-v1") throw new Error("Unknown path encoding");
  return d.replace(/-?[0-9a-z]+/g, token => String(parseInt(token, 36)));
};
```

JSONから必要なデータを読み、ChatCutに渡すMotion Graphicコード内で復元した`d`をSVGの`path`に使う。ChatCutのMotion Graphicはインラインコードとして渡し、`.jsx`ファイルを作成しない。文字を変える場合は新しいテキストでCLIを再実行する。`text_revision.py`はplan内の期待PostScript名を自動照合し、対象cue全文の字形を作り直す。[修正手順](planning.md)を参照。入力propsだけを変えると未知字がCSSの別書体に化ける実装は使わない。

## 検証

```sh
/path/to/work/.glyph-venv/bin/python -B -m unittest discover -s scripts -v
```

同梱テストは架空の院名「青空整体院」を用い、日本語・改行正規化・BOM・半角／全角空白・数字、compactの往復復号と丸め、未収録文字の一覧表示と既存出力保持、不正UTF-8の失敗を確認する。当初の字形テストはPython 3.14 / fontTools 4.66.0で成功。0.3ではフォント違い拒否とテキスト修正時の時刻保持テストを追加している。同じ日本語サンプルを利用者保有のふい字Pでも通常・compactの両形式で確認済み（19文字種、`upem=1024`）。人物・動画素材や案件の文字列はテストへ含めていない。
