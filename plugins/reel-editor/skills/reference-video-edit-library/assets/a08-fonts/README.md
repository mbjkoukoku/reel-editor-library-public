# A08 フォントと互換用派生版

元見本で同定済みの2書体（NotoSerifJP-Black.otf、Corporate-Logo-Rounded-Bold-ver3.otf）はバイト変更なしで保持しています。内部名・著作権・OFL 1.1ライセンスとSHA-256は各LICENSEとfont-manifest.jsonを参照してください。元の2ファイルはファイル名のみ正式PostScript名へ揃えています。

## Corporate OTFが読み込めない環境の互換版

`A08CorpRound-full.otf` は Corporate Logo Rounded ver3 Bold を再ビルドした派生版です。ファミリー名を `A08 Corp Round Full`、PostScript名を `A08CorpRoundFull` に変更しています。元OTFがChatCut Desktopのネイティブレンダラーで読み込みエラーとなる環境用に追加しました。元フォントを正常に読み込める環境へこの独自名を必須にしません。

2026-11-08に、元フォントと派生版の全10,062 Unicode対応、各アウトライン、送り幅を照合し、差分0を確認しました。別の書体への置換ではありません。フォント内部の組み直しと改名を行っているため、元ファイルと同じバイト列ではなく、全OpenType組版機能や全OSで描画が同じことを保証するものでもありません。使用する全文を合成し、文字の形・太さ・サイズ・影・行間を確認してください。

元の著作権表示とOFL 1.1全文は派生版にも保持し、`A08CorpRound-full-LICENSE.txt` を同梱しています。フォント単体販売をせず、共有時は対応する著作権表示とLICENSE全文を必ず同梱してください。

公式配布元・ライセンス確認（2026-11-08）:
- https://logotype.jp/font-corpmaru.html
- https://github.com/notofonts/noto-cjk/blob/main/Serif/LICENSE
- https://openfontlicense.org/open-font-license-official-text/
