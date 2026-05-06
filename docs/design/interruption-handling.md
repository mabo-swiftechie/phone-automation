# 割り込み（バージイン）対応 — 包括的設計ドキュメント

> ステータス: 実装済み（プロンプト層）+ Dashboard設定推奨（プラットフォーム層）
> 最終更新: 2026-05-04

---

## 1. 問題定義

### 現象

AI通話の終了時、全質問への回答をまとめて確認する際、相手が「はい」「そうです」と相槌を打つと、AIが**同じまとめを最初から繰り返す**。これにより通話相手にAIであることが明らかになる。

### 再現条件

1. AIが全質問（空室・外国人・中国人・条件）を完了
2. AIが「確認させていただきますと、[空室状況]で、外国人入居は[可否]...」とまとめ開始
3. 相手が途中で「はい」「ええ」と短い相槌
4. Retell AI が VAD（音声活動検出）で割り込みを検知
5. LLM が相手の入力を受け取り、再度「まとめ」指令を実行
6. **結果**: 同じ内容のまとめが最初から繰り返される

### ビジネスインパクト

- 通話相手の不信感（AIと気づかれる）
- 情報取得の信頼性低下
- 不動産管理会社との関係悪化リスク

---

## 2. 根本原因分析

問題は **2層構造** で発生している。

### 第1層: プロンプト設計（LLMの振る舞い）

**旧コード** (`template_manager.py` DEFAULT_BLOCKS):

```
# 旧「終了ルール」（問題のあった内容）
「確認させていただきますと、[空室状況]で、外国人入居は[可否]、条件は[条件]ですね。
ありがとうございました。失礼いたします。」
```

**問題点**:
- すべての情報を**一括でまとめる**よう指示
- 「割り込まれたらどうするか」の指示がない
- LLMは毎回独立して応答を生成するため、「どこまで言ったか」を覚えていない
- 割り込み後、同じ「まとめ」指令を再実行する

### 第2層: プラットフォーム設定（Retell AI）

Retell AIのデフォルト設定:
- `interruption_sensitivity`: 1.0（最大感度）→ 相槌も割り込みとして扱う
- `denoising_mode`: デフォルト → 背景ノイズによる誤検知の可能性
- バックチャンネル（相槌）設定なし → 「はい」を割り込みと区別できない

**メカニズム**:
1. Retell AI がユーザーの音声活動を検出（VAD）
2. 現在の TTS 再生を停止
3. ユーザーの音声を STT で文字起こし
4. LLM に送信 → LLM が新しい応答を生成
5. LLM は「まとめ」指示を再度実行 → **重複発生**

---

## 3. 実施済み対策

### 3.1 プロンプト改善 ✅

**変更ファイル**: `app/services/template_manager.py`

#### 対話ルールブロック — 追加内容

```
【重要：割り込み（バージイン）対応ルール】
- 自分が発話中に相手が話し始めたら、即座に止まって相手の話を聞く
- 相手の発話が「はい」「ええ」「そうです」等の短い相槌の場合：
  → 直前の発言を繰り返さず、「承知いたしました」と簡潔に応じて次の話題に進む
  → 絶対に、既に言った内容を最初から再度言わない
- 相手が新しい情報や質問を追加した場合のみ：
  → その新しい内容に対して応答し、その後自然に会話を続ける
- 同じフレーズや同じ内容を二度以上繰り返すことを厳禁する
- 各質問への回答が得られたら、その場で「承知いたしました」と即座に確認し、次へ進む（最後の一括まとめはしない）
```

#### 終了ルールブロック — 変更内容

**旧**: 長い一括まとめ → **新**: 簡潔な感謝のみ

```
【終了ルール】
1. 基本的に長いまとめはしない。各質問時にその場で確認済みなので、最後に再度まとめる必要はない
2. 終了時は簡潔に：「本日はお忙しい中ご対応いただき、ありがとうございました。失礼いたします。」
3. 相手が「はい」「わかりました」等で肯定的に応じた場合：即座に感謝を述べて終了
4. 相手が終了前に追加で何か言った場合：「承知いたしました。ありがとうございました。」
5. 相手が急いでいる・忙しそうな場合は、お礼だけ述べて速やかに終了

【終了時の厳守事項】
- 「確認させていただきますと〜」という長いまとめフレーズは使わない
- 既に伝えた情報を繰り返さない
- 相手の相槌に対して同じ内容を二度言わない
```

#### Git差分

```
 app/services/template_manager.py | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
```

### 3.2 設計上の発見

`docs/samples/call_samples.md` の理想通話例には、**もともと長いまとめが含まれていなかった**:

```
AI: 承知いたしました。本日はお忙しい中、ご対応いただき
    誠にありがとうございました。失礼いたします。
```

つまり、旧テンプレートの「終了ルール」は設計意図と矛盾していた。修正により設計意図に整合。

---

## 4. Retell AI 公式パラメータ

以下のパラメータは Retell AI Dashboard（https://www.retellai.com/dashboard → Agents）で設定可能。

### 4.1 割り込み制御

| パラメータ | 範囲 | 推奨値 | 説明 | ドキュメント |
|-----------|------|--------|------|-------------|
| `interruption_sensitivity` | 0〜1 | **0.8** | 割り込み感度。0=割り込み不可、1=最大感度 | [Handle Background Noise](https://docs.retellai.com/build/handle-background-noise) |
| `responsiveness` | 0〜1 | **0.9** | 応答速度。低いほど発話前に余裕を持つ | [Global Settings](https://docs.retellai.com/build/conversation-flow/global-setting) |
| `enable_dynamic_responsiveness` | bool | **true** | ユーザーの話速に動的に適応 | [Global Settings](https://docs.retellai.com/build/conversation-flow/global-setting) |

### 4.2 ノイズ処理

| パラメータ | オプション | 推奨 | 説明 |
|-----------|-----------|------|------|
| `denoising_mode` | `no-denoise` | — | 生音声（テスト用途） |
| | `noise-cancellation` | **推奨** | 背景ノイズ除去（デフォルト） |
| | `noise-and-background-speech-cancellation` | ノイズ環境 | 背景会話も除去（+$0.005/min） |

### 4.3 バックチャンネル（相槌）

| パラメータ | 推奨値 | 説明 |
|-----------|--------|------|
| `enable_backchannel` | **true** | 相槌自動挿入 |
| `backchannel_frequency` | **0.3** | 相槌頻度（高すぎると不自然） |
| `backchannel_words` | **["はい", "承知いたしました", "そうですか"]** | 相槌バリエーション |

### 4.4 音声認識

| パラメータ | 推奨値 | 説明 |
|-----------|--------|------|
| `stt_mode` | **`accurate`** | より正確な文字起こし（〜200ms遅延増加、誤検知削減） |

### 4.5 Conversation Flow ノード設定（Tier 3）

Conversation Flow Agent を使用すると、**ノードごと**に割り込み設定が可能:

| ノード | Block Interruptions | 理由 |
|--------|---------------------|------|
| 挨拶 | **ON** | 挨拶は最後まで話す（信頼性向上） |
| 質問ノード群 | **OFF** | ユーザーの割り込み（訂正・追加情報）を許可 |
| 留守電 | **ON** | メッセージは最後まで話す |
| 終了 | **OFF** | ユーザーの最終確認を許可 |

ドキュメント: [Conversation Node](https://docs.retellai.com/build/conversation-flow/conversation-node)

---

## 5. 割り込み分類マトリクス

業界標準の割り込み分類（[CallSphere](https://callsphere.tech/blog/handling-voice-agent-interruptions-barge-in) より）。

| タイプ | 日本語の例 | AIの適切な対応 | 本プロジェクトでの頻度 |
|--------|-----------|---------------|---------------------|
| **BACKCHANNEL** | 「はい」「ええ」「そうです」「うん」 | 何もせず、続けるか簡潔に終了 | **高**（最頻出） |
| **CANCELLATION** | 「結構です」「やっぱいいです」 | 承知して終了 | 低 |
| **CORRECTION** | 「いや、敷金は2ヶ月です」 | 訂正を受け入れ、記録更新 | 中 |
| **REDIRECT** | 「ところで、駐車場はありますか？」 | 新しい質問に応え、元の流れに戻る | 低 |
| **CLARIFICATION** | 「え、なんて言いました？」 | より明確に繰り返す | 低 |

**重要**: BACKCHANNEL が最も頻出であり、これを正しく処理しないと重複問題が発生する。現在のプロンプト改善は主にこのタイプに対応。

---

## 6. 業界最適プラクティス

### 6.1 プロンプト構造（Retell AI公式推奨）

出典: [Retell AI Prompt Engineering Guide](https://docs.retellai.com/build/prompt-engineering-guide)

```
## Identity
あなたは[会社名]の[役割]です。

## Style Guardrails
簡潔に：1回の発話は2文以内
会話的に：自然な言葉遣い、相槌を入れる

## Response Guidelines
一度に1つの質問のみ：複数質問で圧迫しない
理解を確認：重要情報は簡潔に復唱

## Objection Handling
相手が興味ない：「承知いたしました。...」
相手が焦っている：「本日はありがとうございました。失礼いたします。」
```

### 6.2 短い発話設計（Short Utterance Design）

```
❌ 悪い：「確認させていただきますと、空室はありまして、外国人もOKで...」
         （長文 → 高確率で中断 → 最初から繰り返し）

✅ 良い：各質問後に「承知いたしました」と即時確認。
         最後は「ありがとうございました。失礼いたします。」のみ。
```

### 6.3 他プラットフォームの対応（参考）

| プラットフォーム | 割り込み対応方式 | 特徴 |
|----------------|-----------------|------|
| **Vapi.ai** | `stopSpeakingPlan.acknowledgementPhrases` | 相槌を割り込みと区別（最も詳細） |
| **Bland AI** | プロンプトベース状態追跡 | 「同じ質問を2度するエージェントは信頼を失う」 |
| **OpenAI Realtime** | VAD → `response.cancel` 自動発行 | プロンプトに明示的バラエティルール推奨 |
| **ElevenLabs** | Turn Eagerness (Eager/Normal/Patient) | 環境に応じた3段階調整 |
| **阿里云（中国）** | `<No Interrupting>` タグ | 重要情報の配信中は割り込み不可 |

### 6.4 アンチリピート用プロンプトパターン

出典: [Retell AI Community](https://community.retellai.com/t/prompt-correction/2511)

```
## STYLE
自然に話す（1回の発話は最大2文）
軽いフィラー：「ええ」「なるほど」「承知いたしました」
人間らしく（多少の不完全さOK）

Avoid:
- 長い説明
- ロボット的な応答
- 同じ質問の繰り返し
- 話しすぎ

## RULES
まだ聞いていないことだけ質問する（繰り返さない）
応答は短く
```

---

## 7. KPI（測定指標）

| 指標 | 目標値 | 測定方法 | 説明 |
|------|--------|---------|------|
| 偽停止率 (False Stop Rate) | **< 5%** | 通話録音分析 | 相槌やノイズでAIが停止した割合 |
| 割り込み検出率 | **> 90%** | 通話録音分析 | 本当の割り込みを正しく検知した割合 |
| リピート率 | **0%** | トランスクリプト分析 | 同じ内容を繰り返した通話の割合 |
| 早期切断率 | **< 10%** | call_records分析 | 通話途中で切られた割合 |
| 総パイプライン遅延 (p95) | **< 2秒** | Retell Analytics | 応答までの遅延 |

---

## 8. Retell AIコミュニティ既知問題

### 問題1: 断片的な発話（中途半端に話して最初からやり直す）
- **URL**: https://community.retellai.com/t/issue-fragmented-agent-speech-partial-utterance-plays-then-restarts-from-the-beginning/2498
- **原因**: Function Node で "Speak During Execution" が ON
- **解決策**: Function Node で "Speak During Execution" を OFF、タイピング音を使用

### 問題2: 割り込みが全く効かない
- **URL**: https://community.retellai.com/t/agent-interruption/922
- **原因**: Test Agentは本番と挙動が異なる
- **解決策**: **実際の電話でテスト**（重要）

### 問題3: 最初のメッセージを割り込み不可に
- **URL**: https://community.retellai.com/t/can-the-first-message-be-uninterruptable/862/4
- **解決策**: 最初のノードで "Block Interruptions" を有効化

### ⚠️ 重要な注意事項
- **Test Agentは割り込み設定を反映しない場合あり** — 必ず実際の電話でテスト
- **設定は単独ではなく組み合わせで調整**: `interruption_sensitivity` + `responsiveness` + `denoising_mode` を同時に調整
- **ノイズ環境**: `denoising_mode` を `noise-and-background-speech-cancellation` に設定（+$0.005/min）

---

## 9. テスト計画

### 9.1 Tier 1（Web Call）テスト

1. Streamlit UI > "電話確認" タブ
2. 物件を選択 > "Web Call 開始"
3. AIが質問に回答後、「はいはい」と割り込み
4. **確認**: AIが同じ内容を繰り返さない
5. **確認**: AIが長いまとめなしで簡潔に終了

### 9.2 Tier 2（実電話）テスト

1. Dashboard設定完了後
2. 既知の物件管理会社にテスト通話
3. 意図的に相槌を打つ
4. トランスクリプトで重複を確認
5. `interruption_sensitivity` を 0.6〜1.0 で調整

### 9.3 A/Bテスト

| パターン | interruption_sensitivity | responsiveness | 結果メモ |
|---------|-------------------------|----------------|---------|
| A | 0.8 | 0.9 | （記入） |
| B | 0.6 | 0.9 | （記入） |
| C | 0.8 | 0.7 | （記入） |

---

## 10. 参考リンク

### Retell AI 公式
- [Handle Background Noise](https://docs.retellai.com/build/handle-background-noise)
- [Configure Basic Settings](https://docs.retellai.com/build/single-multi-prompt/configure-basic-settings)
- [Conversation Flow Overview](https://docs.retellai.com/build/conversation-flow/overview)
- [Conversation Node](https://docs.retellai.com/build/conversation-flow/conversation-node)
- [Prompt Engineering Guide](https://docs.retellai.com/build/prompt-engineering-guide)
- [How to Build A Good Voice Agent](https://www.retellai.com/blog/how-to-build-a-good-voice-agent)
- [Turn-Taking Model](https://www.retellai.com/blog/how-retell-ais-turn-taking-model-ensures-seamless-calls)
- [Community Forum](https://community.retellai.com)

### 業界分析
- [CallSphere: Barge-In Handling](https://callsphere.tech/blog/handling-voice-agent-interruptions-barge-in)
- [Callbotics: Interruption Handling](https://callbotics.ai/blog/ai-voice-agent-interruption-handling)
- [VoiceInfra: Prompt Engineering Guide](https://voiceinfra.ai/blog/voice-ai-prompt-engineering-complete-guide)
- [Deepgram: ElevenLabs Barge-In](https://deepgram.com/learn/elevenlabs-barge-in-interruptions-turn-taking)
- [Why Interruptions Break Voice AI](https://medium.com/@raghavgarg.work/why-interruptions-break-voice-ai-systems-5bde68ed60f5)

### 他プラットフォーム
- [Vapi Voice Pipeline Config](https://docs.vapi.ai/customization/voice-pipeline-configuration)
- [Bland Multi-Turn Conversations](https://www.bland.ai/blogs/multi-turn-conversation)
- [OpenAI Realtime Prompting Guide](https://developers.openai.com/cookbook/examples/realtime_prompting_guide)
- [ElevenLabs Conversation Flow](https://elevenlabs.io/docs/eleven-agents/customization/conversation-flow)
