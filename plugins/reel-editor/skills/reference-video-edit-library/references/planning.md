# 可変尺・発話・文字修正の実行手順

**A07（A7）の患者目線Vlogは、このCLIの対象外。** [A07の制作仕様](a07.md)で画面台本と場面表を作り、承認された範囲で患者役素材を調達・生成し、実写の施術者・院内映像と組む。1本内の人物・衣装・時刻の連続性、イメージ映像の表示、今回の確認済み院情報を保ち、固定cue伸縮や全文発話字幕のhelperへ渡さない。文字だけの修正では当該帯・時刻・文字を変更し、映像・音・顔モザイク・イメージ表示を保つ。

**A06（A6）の発話分析・要点デザインは、このCLIの対象外。** [A06の制作仕様](a06.md)で今回の発話内容を分析し、根拠時刻を持つ短い要点と固定デザイン枠を個別に配置する。LPは任意で、先にLP台本を作らない。逐語字幕、参考cueへの固定割付、文字だけを差し替える横書き字幕helperは使わない。必要なカットを反映した完成時刻に要点の表示区間を合わせ、文字修正時も映像・元声・要点の根拠・顔モザイク・表示区間を保つ。

この補助CLIはCodexが案件の作業場所で使う。利用者へJSONやコマンドを書かせない。Python標準ライブラリだけで尺と採用記録を検証し、ChatCutへ配置するための計画を作る。映像認識、ASR、ChatCutへの適用、動画書き出しは行わない。実映像を見ずに`visualReview`を埋めない。

「まず台本だけ」の段階ではこのCLIを使わず、[LPから台本を作る手順](script-first.md)で読み上げ本文とテロップ・仮の映像案を提示する。素材や音声を未確認のままsourceId・使用区間・発話時刻・visualReviewを作らない。実素材と音声を受領し、映像編集へ進む指示を受けてから以下を実行する。

**別のナレーション動画・音声を映像素材に合わせる案件は、このCLIの対象外。** AI音声入り動画でも支給音声を連続した基準にし、[支給ナレーションの手順](provided-narration.md)で音声・映像・字幕を独立して配置する。下記の見本順・1役割1範囲・映像に連動する発話処理をその経路へ当てはめない。ファイル名の番号は内容と順番の手掛かりであり、`referenceCut`へ直接変換しない。

**A03の音声なし・縦横混在の編集も、このCLIの対象外。** [A03の制作仕様](a03.md)で、承認済みテロップと映像を独立して配置する。A03を入れると計画・文字修正helperはエラーにし、横書き用の検証を通ったと扱わない。

**A04もこのCLIの対象外。** フィラーカット後の発話時刻を[a04.md](a04.md)に従って配置する。見本の61個のcueや尺へ固定しない。

**A05の施術前後比較もこのCLIの対象外。** [A05の制作仕様](a05.md)で、確認済みの前後対応・画角・表示ラベル・LP配色・顔モザイクを個別に配置する。見本の約47.8秒や固定cueへ割り付けず、無音を基準に動作時間を削らない。文字だけの修正もA05専用手順で行い、映像・前後対応・モザイク・開始終了を保つ。

## 素材から計画を作る

1. 今回の素材を取り込み、現在のsourceId、実尺、開始・中間・終了付近の画像、採用区間全体の動きを確認する。秒数は元ファイルの時刻。異なるfpsの素材でも選択パターンの`canvas.fps`へ換算し、速度は1倍のまま。
2. 選択パターンのJSONにある`cuts`の0起点インデックスを`referenceCut`へ指定し、相当する役割を割り当てる。A01は0〜12。A02など別のパターンではその`cuts`を読み、A01の番号・外観の位置・フォントを流用しない。順番を保持し、不要な役割は省略できる。1役割につき1つの連続範囲をこのhelperに入力する。複数のカットに分けたい場合は生成後に計画と文字・音声の対応を整え、同じ検証を行う。helperが扱わないBロールと別録音の同期を「自動で済んだ」と扱わない。
3. カットに応じた文章を準備し、下記形式を今回の作業場所へ保存する。`pattern`は利用者が選択したID（A01、A02など）。省略時は既存依頼との互換性のためA01になる。記載例は入力の形だけを示すもので、完成動画の台本ではない。

```json
{
  "pattern": "A01",
  "mode": "reference",
  "shots": [
    {
      "referenceCut": 0,
      "sourceId": "CURRENT_IMPORTED_ASSET_ID",
      "sourceInSeconds": 1,
      "sourceOutSeconds": 5,
      "sourceDurationSeconds": 20,
      "visualReview": {
        "continuousChecked": true,
        "motionNote": "採用区間を通して施術者が患者の肩を動かしている",
        "samples": [
          {"sourceSeconds": 1, "practitionerVisible": true, "treatmentVisible": true, "evidence": "施術者の上半身と肩への手が見える"},
          {"sourceSeconds": 3, "practitionerVisible": true, "treatmentVisible": true, "evidence": "患者の腕を支えて動かしている"},
          {"sourceSeconds": 4.9, "practitionerVisible": true, "treatmentVisible": true, "evidence": "施術者と施術の手元が画面内に残る"}
        ]
      }
    }
  ],
  "texts": {
    "text0": {"text": "肩のお悩みを\n相談できます", "source": "今回LPの相談対象の記述"},
    "text1": {"text": "今回の確認済み本文", "source": "今回LPの該当URLまたは提供情報"}
  }
}
```

必須の施術者と施術を見本の同じ構図に寄せつつ、画面から外れない範囲を選ぶ。無人の映像は、そのパターンの`visualSelection.unoccupiedAllowedRoles`に列挙された役割だけで、`emptyBridgeReason`を添えた短い区間を使える。A01は外観・内観（referenceCut 2/3）が対象。別パターンへこの番号を当てはめない。尺の制限も同じ`visualSelection`の設定を使い、記載がなければ1本2秒・連続4秒。案件の明確な意図で変える場合は`visualLimits.maxUnoccupiedShotSeconds` / `maxUnoccupiedRunSeconds`へ記録し、理由も案件メモへ残す。

A02の患者の動作確認など、`allowPatientOnlyRoles`に指定された役割では施術者が映っていなくても使える。各sampleの`practitionerVisible`・`treatmentVisible`は事実どおりfalseにし、実際に見える人物について`personVisible:true`（患者と確認できれば`patientVisible:true`でも可）とevidenceを記録する。別の役割へこの例外を広げない。全体には施術者と実際の施術が映る動画が必要。

`optionalLicensedImageRoles`の役割は、今回提供された利用可能な画像を明示的に使うか、今回の人物・施術映像で置き換えるか、区間を省く。画像の場合はshotに`sourceMediaType:"image"`と`imageUsageEvidence:"利用許可を確認した根拠"`を付け、各sampleに`personVisible`と見た内容を記録する。静止画のsourceIn/Out/DurationSecondsはその画像に割り当てる表示区間で、実ファイルの録画尺とは扱わない。画像だけで全体の施術者・実際の施術の要件を満たしたことにしない。動画は`sourceMediaType:"video"`（省略時もvideo）。見本の静止画を別店舗へ転用したり、ストック素材を勝手に取得・生成したりしない。

```sh
python3 scripts/timeline_plan.py /path/to/job/request.json --output /path/to/job/plan.json
```

CLI側で`--pattern A02`も指定できる。request内にも`pattern`がある場合は一致が必要。未登録ID、パス名、別パターンのJSONとの食い違いはエラーにし、既存の出力を書き換えない。

`texts`に入れたcueだけを配置する。原稿にない文章・旧店舗の情報は自動で補わない。省いたsceneに対応するcueは落とし、警告へ記録する。文字を削りすぎると内容が伝わらないので、planを読んで台本として確認する。各パターンのcueと装飾区間は採用sceneの尺へ再計算される。見本で同時に表示される別レイヤーの文字は重ねたまま保持する。装飾は初期値`enabled:false`で、今回の根拠・素材がある場合だけ有効化する。

`originalCapCut`などのアニメーション原記録は変更せず保持する。`appliedAnimations`には今回のcue内のローカルフレームで`startFrame`、`durationFrames`、`endFrame`を出す。0.5秒の導入なら通常はその速度を維持し、cue自体が短いときだけ収まる長さへ制限する（`clamped:true`と警告）。退出はcueの終端へ合わせる。開始待ち時間がcueを超える動きは省略して警告する。ChatCutへはこの計算済み時刻を使い、合成で動きと読みやすさを確認する。見本JSONでフレーム単位の動きを直接保存するときは`animations:[{type:"in",startFrame:0,durationFrames:15,...}]`を使える。

読速の目安は毎秒8文字を超えたら警告。これは機械的な目安であり、固有名詞を読めるか実際に確認する。`needsLayoutReview`は1行12文字超またはパターンの行上限超を知らせる補助。A02承認版は最大2行で3行以上をレビュー対象にする。A01は従来どおり4行以上を対象にし、フォントの実幅測定は後段で行う。A02の出力には`productionProfile`を保持し、承認版の位置・色・動き・検証方針をそのまま適用する。原見本の観測JSONを読み直して旧設定へ戻さない。警告を放置して完成報告しない。

出力の`cuts[].start/end`、`cues[].start/end`は選択パターンの`canvas.fps`でのフレーム数、終了を含まない。`sourceInSeconds/sourceOutSeconds`は元ファイルの秒。各MGが区間開始からのローカルフレームを使う場合、タイムライン上のstartを二重加算しない。

## 本人の声をそのままテロップ化する

この節は、採用する映像と同じ素材に入っている発話を一緒に編集する場合の手順。別の支給ナレーションへ複数の素材映像を重ねる場合は、上記の専用手順を使う。

先に[speech-cleanup.md](speech-cleanup.md)のフィラー・長い間の整理を行う。カットが必要な案件はScriptを通して実際の再生区間を編集し、整理後のタイムラインへ字幕を作る。以下のhelperの例は整理が不要な場合、またはカット不要の明示指定がある場合に使う。helper自体はフィラーや無音を検出せず、整理前の計画で消した発話を復活させない。

現在のChatCutの文字起こし手順を使い、原音で誤認識を直す。1文を無制限に長い字幕へ入れず、息継ぎ・意味の切れ目ごとに短い`speechSegments`へ区切る。A02は最大2行、A01は画面上の2〜3行を目安にするが、単語の途中は切らない。文章を短く要約して合わせず、複数の字幕へ分ける。LPは店名・地域・連絡先の確認に使い、本人の発言をLP文へ勝手に言い換えない。

`mode`を`verbatim_speech`とし、`texts`の代わりに以下を追加する。`shots`と実映像確認は同じ形式。

```json
{
  "speechSegments": [
    {
      "sourceId": "CURRENT_IMPORTED_ASSET_ID",
      "startSeconds": 1.2,
      "endSeconds": 3.9,
      "text": "肩の動きを確認します。",
      "words": [
        {"startSeconds": 1.2, "endSeconds": 2.0, "text": "肩の動きを"},
        {"startSeconds": 2.1, "endSeconds": 3.9, "text": "確認します。"}
      ]
    }
  ]
}
```

`words`の連結は`text`と完全一致させる（句読点・空白を含む）。元音声の正確な単語時刻を取得できる場合に使い、タイミングを均等配分して創作しない。全発話が採用区間に収まる場合のみwords省略可。カットが単語を切断する、時刻が重なる、同じソースの発話を逆順・重複で使う場合はエラーになる。カット位置または原音に基づく単語時刻を直す。

helperは採用区間に残る言葉だけを完成時間へ移し、元声のミュートを解除する。文字の見た目はパターンの`speechCaptionCueKey`が指すcueを優先し、未設定なら同じ役割と重なる、または最も近い計測済み本文cueを使う。手書きの導入・バッジ専用cueは本文へ流用しない。文字ごとのフォント識別名・影・アニメーションなども保持する。ChatCutへ適用後、採用された声が原音と同じであり字幕と同期することを連続再生で確認する。声とBロールを別トラックで組む案件は音声のsource→timeline対応を別に管理する必要がある。

## 元フォントと字形の準備

選択パターンの`plan.typography.bodyPostscriptName`と`introPostscriptName`を確認する。cueに`postscriptName`がある場合はその指定を優先する。A01は本文`VDL-V7Mincho-Ultra`、導入`HuiFontP`であり、別パターンへ決め打ちしない。[fonts.md](fonts.md)で利用可能なファイルを確認し、`glyphs.py --expected-postscript-name ...`で別の字体の誤投入を拒否する。原稿の影パラメータはCSSと別単位。plan内の仮CSSを完成値とせず、元動画の文字と影の領域を合成プレビューで比較して較正する。

ユーザーが明示的にNoto代替を選んだ案件のみ、requestへ`typographyFallback:"noto"`と`fontFallbackApprovedByUser:true`を記録できる。本文の既定字体だけを代替し、導入やcue固有の`postscriptName`は変更しない。出力は`defaultFidelity:"user-approved-approximation"`となり、同じフォントとは扱わない。承諾の記録をCLIの都合で勝手にtrueへしない。

## 文字だけを修正する

```sh
/path/to/python-with-fonttools scripts/text_revision.py --plan /path/to/job/plan.json --cue text5 --text /path/to/job/revised-text.txt --font /path/to/usable-font.ttf --output /path/to/job/text-revision.json
```

指定cue全文の字形を作り直し、期待フォントを照合し、改行を保った実幅と推奨縮小率を出す。TTC/OTCは実名を確認したface番号を`--font-number`へ渡す（省略時0）。A02の明朝W6が別faceにある環境で、先頭の別書体を選ばない。幅上限は`cue.metrics.maxLineAdvance`を優先し、なければパターンの`typography.maxLineAdvance`を使う。未知文字・字体の不一致・未特定のフォントがあれば既存出力を上書きしない。文字変更後もカット・音声・cueの開始終了は保持する。字幕が長くなって読めない場合は、この文字修正とは別に尺変更を計画する。

Codexは出力のcueのtextとglyphsを現在のChatCut編集ツールで反映する。MGの字形方式と、ChatCutの標準captionカードの方式は区別する。標準captionの内容変更には専用のtext編集操作を使い、Transcriptの単語削除を使わない。枠に収まるか・影が変わらないかを合成で確認し、planの`chatcutApplied`や`composedFramesVerified`を実行前にtrueにしない。

## このCLIで保証しないこと

人や施術を自動認識しているわけではなく、Codexが実映像から作った確認記録と使用時刻の整合性を検査する。元フォントを用いた新しいChatCut描画・他アカウントへの導入・MP4出力の成功は別の検証。`verification`でこれらを明確に分ける。
