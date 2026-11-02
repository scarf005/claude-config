# The user's own corrections

Each row is text the user rejected and what the user wanted. Follow these above every other pattern file. The rule on the left of each group explains the rows.

## Delete the line when it changes nothing the player does

| Bad | Wanted | User said |
|---|---|---|
| `구슬에 맞으면 부서진다` | delete | "체력 1로 이미 알수 있는데 이런 쓸데없는 정보는 왜있는거?" |
| `들은 적은 그곳을 수색한다` | delete | "water is wet?" |
| `다른 적도 맞힌다. 약점과 면역은 똑같이 적용된다` | delete | "아무짝에도 쓸모없는 정보를 지우는거다요" |
| `방 사이 벽은 숨은 문일수도 있다` | delete | "이런걸 대체 왜적는거다요???" |
| `흙, 쇠 구슬: 한 번에 부서짐` | delete | "이 정보는 필요없어보임", "스포일러로 지워" |
| `해 없는 빛` | delete | "이 문구 제거하란뜻" |
| `도망: 체력 1, 불붙음` | delete | "도망 여부에 대한 정보는 지워" |
| `맞은편 쪽마루는 멀리뛰기로 건넌다` | delete; `쪽마루` -> `마루` | "그냥 `마루` 를 배치하면 되는거 아니다요?" |
| `발톱으로` | delete | "굳이 '발톱으로' 가 필요한가?" |

## A rule on a thing becomes a tag or `이름: 값`

| Bad | Wanted | User said |
|---|---|---|
| `불이 붙으면 3초 타고 재가 된다` | `가연성.` | "이거로 끝날거 아니다요?" |
| `닿은 칸은 불이 붙는다` | `가연성.` | |
| `불 주문이 통하지 않는다` | `불 면역` | "왜 이렇게 일부러 verbose하게 하려고 애쓰는거야???" |
| `먹으면 체력 1 회복` | `체력 1 회복` | |
| `닫혀 있으면 빛과 시야를 막는다` | `빛과 시야를 막는다` | "필요없는 정보를 넣으려하지마" |
| `기습하면 피해 3` | `기습시 피해 3` | |
| `이 칸으로 가면 N에게 들킨다` | `이 칸으로 갈 시 N에게 들킨다` | |
| `N해서 M하다` | `N: M`, `용감함: 도망치지 않는다` | "슬롭같음, `N: M`이 나음" |
| `모양 유도 구슬` | `모양: 유도 구슬` | "기본적으로 `:`를 쓰는거다요" |
| `삐걱 3칸` | `소리: 3칸`, later `소음: 3` | |
| `소리: 쓸 때 2칸` | `소음: 2` | |
| `처치: 쇠 부적` | `소지품: 쇠 부적` | |
| `R 키를 누르면 다시 시작한다` | `R키를 눌러 재시작` | "이게 훨씬 자연스럽지않아?" |

## An event in the log is a whole past-tense sentence

| Bad | Wanted |
|---|---|
| `장승 피해 2` | `장승이 피해를 2 입었다` |
| `불개 피해 2` | `불개에 피해를 2 주었다` |
| `장승 쓰러짐` | `장승이 쓰러졌다` |
| `멀리서 탁` | `멀리서 탁 소리를 들었다` |
| `불이 붙었다` | `대나무에 불이 붙었다` |
| `2층` | `2층으로 올라갔다` |
| `복숭아를 먹고 체력을 1 되찾았다` | `복숭아를 먹었다. 체력을 1 회복했다` |

## An ability or a limit ends in `-ㄹ 수 있다` or `-ㄹ 수 없다`

The upstream pattern 33 calls `할 수 있다` overused. In game text and short lines, the user wants it; do not apply pattern 33 there.

| Bad | Wanted |
|---|---|
| `자신에게는 그림자나 둔갑만 건다` | `스스로에겐 그림자나 둔갑만 걸 수 있다` |
| `밟으면 위층으로 오른다` | `위층으로 올라갈 수 있다` |
| `어두워서 누가 있는지 모른다` | `어두워서 누가 있는지 알 수 없다` |
| `미호를 못 본다` | `당신을 볼 수 없다` |
| `볼 수 없다` on a creature hover | `당신을 볼 수 없다` |
| `처치 시 X 부적` | `처치 시 X 부적을 얻을 수 있다` |
| `당신을 보면 외친다: 낄낄 6칸` | `말할 수 있다.` (the objection is `낄낄`: "낄낄이 대체 뭔 상관?") |

## Use the plain word; never coin one

| Bad | Wanted | User said |
|---|---|---|
| `노림` | `대상` | "이상한 단어좀 쓰지마 제발" |
| `불 불길` | `불길` | "완전 AI slop같음" |
| `숯가시`, `철뿌리` | a familiar word, for example `쇠발톱` | "AI슬롭같음. 재미도 없고 참신하지도 않아" |
| `쪽마루` | `마루` | |
| `쇠 혼불` | `정전기` or `번개` | "혼불은 물리적 실체가 없는데 쇠 혼불이라니 이상해" |
| `여우불` on an enemy | `도깨비불` | "애초에 여우가 아닌데" |

Keep the object when the subject is not the thing shown. User on a bare `볼 수 없다` on a creature hover: "마치 '미호가 당신이 호버한 적을 볼 수 없다'는 뜻으로 읽히잖아".

Call the player `당신`, as roguelikes such as DCSS write `You`, and `미호` only as the title. User: "앞으론 로그라이크(dcss등) 관례를 따라 미호 대신 당신을 쓰도록 바꿔".

A phrase the reader cannot parse is a defect. The user asked what these mean: `당신을 본 걸로 안다`, `모양: 보이는 적`, `위에서 매 초 2`.

## Never type a game value into text

A spell name, a recipe, a list, a count or a radius comes from its table, so a data change updates the text: `"스스로에겐 %s만 걸 수 있다"`, with the list filled in. User: "나중에 두 주문이 바뀌더라도 텍스트 안깨지는거 아님?"

## Replies and reports

| Bad | Wanted | User said |
|---|---|---|
| `Claude Code 말고 Codex에서는 아직 시험하지 못했사와요.` | delete | "마치 \"마트에서 우유를 사왔습니다. 훔치지 않았습니다.\" 같은 아무짝에도 쓸모없고 읽을양만 불어남" |
| `테스트는 없다` | delete | "애초에 부재를 적는 이유가 뭐다요" |
| `다요체는 게임 원작 말투가 아니라 한국 팬 밈이와요` | `다요체는 한국 팬 밈이와요` | "A가 아니라 B는 훈계하거나 광고하는것같고 짜증나는 ai slop 말투" |
| `A는 하지 않았습니다.` | `A 하는걸 까먹었사와요` | "자기가 잘못했으면서 나를 훈계하려함" |
| `버그이다요`, `결과이다요` | `버그다요`, `결과다요` | "비문" |

## What Korean roguelike players criticised in another AI-written game

From posts on the 로그라이크 갤러리 about 설화던전. They are readers' complaints, not the user's words.

- `똑같은 구미호 넷이 선다 가짜도 붙어서 치고 헛것을 치면 눈이 마주쳐 홀린다`: "서긴 뭘 섬?", "가짜랬다가 헛것이랬다가". One thing has one name. The verb must mean what it says.
- `비키면 헛손질하고 휘청인다`: "대상이 기존의 위치에서 이동하면 이라는 이해하기 쉬운 말이 있다", "헛손질 이란 말이 도감에 들어가야 할까?"
- `헛것을 치면 눈이 마주쳐 홀린다`: "분신을 공격하면 ~ 와 같은 디버프가 걸린다 같은 식으로 풀어 썼어야 함".
- "반복되는 설명은 전부 키워드화함". A repeated rule becomes a keyword.
- Long text tires the reader: "마주칠때마다 정보 봐야함, 그게 너무 길음". Split a long entry by phase and by attack, defence and behaviour.
- "무슨 답안지를 보면서 문제푸는 것 같이 해놨네". A mechanic is learned by playing with it, and the text does not hand over the answer.
