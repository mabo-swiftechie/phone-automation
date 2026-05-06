# AI電話 割り込み（バージイン）対応 — 最適解ガイド

> **注意**: 本ドキュメントの内容は以下の正式設計ドキュメントに統合されました。
> - **包括的設計ドキュメント**: [docs/design/interruption-handling.md](design/interruption-handling.md)
> - **3段階ソリューション**: [docs/design/solution-tiers.md](design/solution-tiers.md)
>
> 本ドキュメントは参照用として残しています。最新情報は上記を参照してください。

> 更新: 2026-05-03

## 問題

AI通話の終了時、全質問への回答をまとめて確認する際、相手が「はい」「そうです」と相槌を打つと、AIが**同じまとめを最初から繰り返す**現象が発生。明らかにAIと分かってしまう。

---

## 実施済み対策（コード変更）

### 1. プロンプト改善 ✅

`app/services/template_manager.py` の DEFAULT_BLOCKS を変更：

**対話ルール** — 以下を追加：
- 割り込み（バージイン）対応ルール
- 相槌への簡潔な応答（「承知いたしました」のみ）
- 同じ内容の繰り返し厳禁
- 各質問時に即時確認（最後の一括まとめ不要）

**終了ルール** — 以下に変更：
- 一括まとめを廃止
- 「本日はお忙しい中ご対応いただき、ありがとうございました。失礼いたします。」で終了
- 「確認させていただきますと〜」の長フレーズ禁止

---

## Retell AI 公式パラメータ（Dashboard → Agent設定 で調整）

### 必須設定

| パラメータ | 範囲 | 推奨値 | 説明 |
|-----------|------|--------|------|
| `interruption_sensitivity` | 0〜1 | **0.8** | 割り込み感度。低いほど割り込みにくい。ノイズ誤検知防止 |
| `responsiveness` | 0〜1 | **0.9** | 応答速度。低いほど発話前に余裕を持つ |
| `denoising_mode` | 3種 | **`noise-cancellation`** | 背景ノイズ/会話除去。誤った割り込み検知を防ぐ |
| `enable_dynamic_responsiveness` | bool | **true** | ユーザーの話速に動的に適応 |

### 推奨追加設定

| パラメータ | 推奨値 | 説明 |
|-----------|--------|------|
| `enable_backchannel` | **true** | 相槌自動挿入（自然度向上） |
| `backchannel_frequency` | **0.3** | 相槌頻度（高すぎると不自然） |
| `backchannel_words` | **["はい", "承知いたしました", "そうですか"]** | 相槌バリエーション |
| `stt_mode` | **`accurate`** | より正確な文字起こし（〜200ms遅延増） |

**設定方法**: https://www.retellai.com/dashboard → Agents → 対象Agent

**公式ドキュメント**:
- https://docs.retellai.com/build/handle-background-noise
- https://docs.retellai.com/build/single-multi-prompt/configure-basic-settings
- https://docs.retellai.com/build/conversation-flow/global-setting
- https://docs.retellai.com/build/interaction-configuration

---

## 業界最適プラクティス（Retell AI公式推奨）

### プロンプト構造（公式推奨フォーマット）

```
## Identity
あなたは[会社名]の[役割]です。

## Style Guardrails
簡潔に：1回の発話は2文以内
会話的に：自然な言葉遣い、相槌を入れる
丁寧に：相手の状況に配慮する

## Response Guidelines
日付は話し言葉で：「1月15日」ではなく「1月15日」
一度に1つの質問のみ：複数質問で圧迫しない
理解を確認：重要情報は簡潔に復唱

## Objection Handling
相手が興味ない：「承知いたしました。...」
相手が焦っている：「本日はありがとうございました。失礼いたします。」
```

出典: https://docs.retellai.com/build/prompt-engineering-guide

### 短い発話設計（Short Utterance Design）

```
❌ 悪い：「確認させていただきますと、空室はありまして、外国人もOKで、敷金は...」
         （長文 → 高確率で中断 → 最初から繰り返し）

✅ 良い：各質問後に「承知いたしました」と即時確認。
         最後は「ありがとうございました。失礼いたします。」のみ。
```

### 確認疲れ（Confirmation Fatigue）回避

人間は同じ内容を2回以上確認されると「機械だ」と感じる。一度確認した内容は再言及しない。

### Conversation Flow の活用

Retell AIのConversation Flow Agentを使用すると、**ノードごとに割り込み設定**が可能：
- 挨拶ノード：Block Interruptions = ON（最初の挨拶は最後まで話す）
- 質問ノード：Block Interruptions = OFF（ユーザーの割り込みを許可）
- 終了ノード：Block Interruptions = OFF

出典: https://docs.retellai.com/build/conversation-flow/overview

---

## Retell AIコミュニティで報告された関連問題と解決策

### 問題1：断片的な発話（中途半端に話して最初からやり直す）
- **URL**: https://community.retellai.com/t/issue-fragmented-agent-speech-partial-utterance-plays-then-restarts-from-the-beginning/2498
- **原因**: Function Nodeで "Speak During Execution" がON。ツール呼び出しが完了すると、Agentの発話が中断され、同じ内容を最初から再生成
- **解決策**: Function Nodeで "Speak During Execution" をOFFに。タイピング音を使用

### 問題2：割り込みが全く効かない
- **URL**: https://community.retellai.com/t/agent-interruption/922
- **原因**: Test Agentは本番と挙動が異なる。`denoising_mode` が不適切
- **解決策**: 実際の電話でテスト。denoising_modeとinterruption_sensitivityを組み合わせて調整

### 問題3：最初のメッセージを割り込み不可にしたい
- **URL**: https://community.retellai.com/t/can-the-first-message-be-uninterruptable/862/4
- **解決策**: 最初のノードで "Block Interruptions" を有効化

### ⚠️ 重要な注意事項
- **Test Agentは割り込み設定を反映しない場合あり** — 必ず実際の電話でテスト
- **ノイズ環境では** `denoising_mode` を `noise-and-background-speech-cancellation` に設定（+$0.005/min）
- **設定は単独ではなく組み合わせで調整**: `interruption_sensitivity` + `responsiveness` + `denoising_mode` を同時に調整

---

## アンチリピート用プロンプトパターン（コミュニティ実証済み）

出典: https://community.retellai.com/t/prompt-correction/2511

```
## STYLE
自然に話す（1回の発話は最大2文）
軽いフィラーを使う：「ええ」「なるほど」「承知いたしました」
人間らしく聞こえる（多少の不完全さOK）
相手のトーンに合わせる

Avoid:
- 長い説明
- ロボット的な応答
- 同じ質問の繰り返し
- 話しすぎ

## RULES
まだ聞いていないことだけ質問する（繰り返さない）
応答は短く
混乱したら → シンプルに確認
沈黙したら → フォローアップ質問
```

---

## テスト計画

1. **新規インストール**: 起動時に新しいテンプレートが自動適用される
2. **既存DBがある場合**: Streamlit UI → Templates → 各Blockを手動更新
3. **テスト手順**:
   - Web Callでテスト通話を開始
   - AIが「承知いたしました」と言った直後に「はいはい」と割り込み
   - AIが同じ内容を繰り返さないことを確認
   - 最後に長いまとめがなく、簡潔に終了することを確認
4. **Retell Dashboard設定**:
   - Agent設定で上記パラメータを調整
   - 実際の電話でテスト（Test Agentは正確でない場合あり）

---

## 他プラットフォームの割り込み対応（参考）

### Vapi.ai（最も詳細な設定）

```json
{
  "stopSpeakingPlan": {
    "numWords": 0,
    "voiceSeconds": 0.2,
    "backoffSeconds": 1.0,
    "acknowledgementPhrases": ["okay", "right", "uh-huh", "yeah", "mm-hmm"]
  }
}
```

- `acknowledgementPhrases`: 相槌は割り込みとして扱わない（重要！）
- `backoffSeconds`: 割り込み後の待機時間

出典: https://docs.vapi.ai/customization/voice-pipeline-configuration

### OpenAI Realtime API

- VADがユーザー発話を検出 → `response.cancel` 自動発行
- `conversation.item.truncate` で未再生音声をコンテキストから除去
- プロンプトに明示的なバラエティルール推奨:
  ```
  ## Variety
  - Do not repeat the same sentence twice.
  - Vary your responses so it doesn't sound robotic.
  ```

出典: https://developers.openai.com/cookbook/examples/realtime_prompting_guide

### Bland AI（状態追跡アプローチ）

「同じ質問を2度するエージェントは信頼を失う」— 多ターン状態追跡を推奨：
- ユーザー意図の追跡
- 既に収集した情報の追跡
- まだ必要な情報の追跡
- 会話フェーズの追跡

出典: https://www.bland.ai/blogs/multi-turn-conversation

---

## 割り込みの分類（本プロジェクトに適用可能）

| タイプ | 例 | AIの対応 |
|--------|-----|---------|
| **BACKCHANNEL** | 「はい」「ええ」「そうです」 | 何もせず、続けるか簡潔に終了 |
| **CANCELLATION** | 「やっぱいいです」「結構です」 | 承知して終了 |
| **CORRECTION** | 「いや、敷金は2ヶ月です」 | 訂正を受け入れ、記録更新 |
| **REDIRECT** | 「ところで、駐車場は？」 | 新しい質問に応え、元の流れに戻る |
| **CLARIFICATION** | 「え、なんて言いました？」 | より明確に繰り返す |

出典: https://callsphere.tech/blog/handling-voice-agent-interruptions-barge-in

---

## 本番運用のKPI（指標）

| 指標 | 目標値 | 説明 |
|------|--------|------|
| 偽停止率（False Stop Rate） | < 5% | 相槌やノイズでAIが停止する割合 |
| 割り込み検出率 | > 90% | 本当の割り込みを正しく検知する割合 |
| リピート率 | 0% | 同じ内容を繰り返した通話の割合 |
| 早期切断率 | < 10% | 通話途中で切られる割合 |
| 総パイプライン遅延 (p95) | < 2秒 | エンドポイント+LLM+TTS合計 |

---

## 参考

### Retell AI
- [Handle Background Noise](https://docs.retellai.com/build/handle-background-noise)
- [Configure Basic Settings](https://docs.retellai.com/build/single-multi-prompt/configure-basic-settings)
- [Conversation Flow Overview](https://docs.retellai.com/build/conversation-flow/overview)
- [Prompt Engineering Guide](https://docs.retellai.com/build/prompt-engineering-guide)
- [Interaction Configuration](https://docs.retellai.com/build/interaction-configuration)
- [How to Build A Good Voice Agent](https://www.retellai.com/blog/how-to-build-a-good-voice-agent)
- [Turn-Taking Model](https://www.retellai.com/blog/how-retell-ais-turn-taking-model-ensures-seamless-calls)
- [Community Forum](https://community.retellai.com)

### 他プラットフォーム
- [Vapi Voice Pipeline Config](https://docs.vapi.ai/customization/voice-pipeline-configuration)
- [Vapi Prompting Guide](https://docs.vapi.ai/prompting-guide)
- [Bland Multi-Turn Conversations](https://www.bland.ai/blogs/multi-turn-conversation)
- [Bland Prompting Guide](https://www.bland.ai/blogs/prompting-guide-ai-phone-calls)
- [OpenAI Realtime Prompting Guide](https://developers.openai.com/cookbook/examples/realtime_prompting_guide)
- [ElevenLabs Conversation Flow](https://elevenlabs.io/docs/eleven-agents/customization/conversation-flow)

### 業界分析
- [CallSphere: Barge-In Handling](https://callsphere.tech/blog/handling-voice-agent-interruptions-barge-in)
- [Callbotics: Interruption Handling](https://callbotics.ai/blog/ai-voice-agent-interruption-handling)
- [VoiceInfra: Prompt Engineering Guide](https://voiceinfra.ai/blog/voice-ai-prompt-engineering-complete-guide)
- [Deepgram: ElevenLabs Barge-In](https://deepgram.com/learn/elevenlabs-barge-in-interruptions-turn-taking)
- [Why Interruptions Break Voice AI (Medium)](https://medium.com/@raghavgarg.work/why-interruptions-break-voice-ai-systems-5bde68ed60f5)
- Shah (2026) "Strategies for Handling Barge-in Interruptions in Conversational AI Interfaces"

### 中国語圏の参考
- [阿里云: 智能体打断处理](https://help.aliyun.com/zh/ims/user-guide/how-to-avoid-interruptions-during-agent-responses)
- [腾讯云 TRTC: 打断机制](https://cloud.tencent.com/document/product/647/112472)
