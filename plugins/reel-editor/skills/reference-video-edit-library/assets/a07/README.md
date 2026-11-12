# A07 承認済み描画資産

0.10.5・2026-11-10の完成承認版。先に [制作基準](../../references/a07-approved-profile.md) と [数値仕様](../../references/a07.json) の `productionDefaults` を読む。

- `a07-approved-layout.desktop.jsx`：承認されたDesktop用描画ソース。画面の本文・時刻・帯・影は独立した編集可能propertiesで扱う。画像・動画・音・患者役はこのファイルに含めない。
- `a07-approved-layout.properties.json`：最終承認値に更新したproperty一覧。旧制作ファイルの72px／78px等を使わない。院名・地域・本文・時刻・AI／サンプル表示は空で、今回の承認済み台本を設定する。
- `a07-approved-role-overrides.json`：導入・本文・分割帯・調べる場面・院内・締めの上書き値。素材IDや秒数は固定しない。導入は全体フォントを本文と同じ700へ変え、時計は既定900を保つ。
- `fonts/A07ReferenceSerif-Bold.otf`：本文・導入・終盤用。Noto Serif CJK JP Boldの字形を保持し、既存Black書体との名前衝突を避けて **A07 Reference Serif** へ改名したOFL1.1派生版。
- 時計の900は既存同梱 `../fonts/NotoSerifCJKjp-Black.otf`（Noto Serif CJK JP）を使う。本文700と時計900を取り違えない。

このJSXは、実際に承認されたDesktopのReact/Remotion import・export構文を保持している。使う接続のMotion Graphicスキルを読み、現行Desktopの対応方法でソースを登録する。Web用の `Component`／注入globals契約とは異なるため、Webへそのまま渡さない。必要なら現行ホスト契約にだけ合わせて変換し、実際の合成と書き出しを確認する。描画値まで変えない。

フォントは現行ChatCutレンダラーへ登録し、読み戻したfamily・weightと描画を確認する。本文78px／行送り104px、時計75px／100px、終盤90px／118pxを保ち、長文は意味単位で次のcueへ分ける。新しいpropertiesだけでは過去のitem overridesを消せないため、再利用プロジェクトでは古い72／78等の上書きが残っていないか確認する。

## フォントの配布条件

`fonts/NotoSerifCJK-LICENSE.txt` と `fonts/DERIVATIVE-NOTICE.txt` を同梱し、元の著作権・ライセンス情報を保持する。フォントはOFL1.1のまま配布し、単独販売しない。元見本の書体を同定したという意味ではない。制作時の名前衝突対策であり、第三者環境の描画検証済みという意味でもない。

元BGM・効果音・クリニック映像・患者役映像は同梱しない。今回の原音利用許可を第三者再配布許可へ拡張しない。音の配置・音量の方針は数値仕様を使い、その制作で使える音源へ同期する。
