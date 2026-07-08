# AI News Digest: Video qtzzN8w2TvU

**Video URL:** https://www.youtube.com/watch?v=qtzzN8w2TvU
**Published Date:** 2026-07-08

---

## Top Ranked Stories

### Rank 1: AI news intro

**Model's Reasoning:** *Fell back to chronological order due to LLM failure.*

**Timestamp:** [0s](https://youtu.be/qtzzN8w2TvU?t=0)

#### Transcript Excerpt:
> AI never sleeps and this week has been absolutely insane. Your full body waifu is finally here. This Chinese food delivery company just trained a Frontier model without any Nvidia GPUs, which is a huge deal. Claude Fable 5 is back. It's now available globally, but it does have some additional nerfing which you need to be aware of. Google released some super efficient image and video models. We have a new AI that can understand sheet music. This AI can edit videos in real time. Meta released an AI that can turn your thoughts into text. So now you can just type by thinking. We have some new ways to speed up image models by over 20 times. This AI can turn a photo into a full physically accurate 3D simulation. We have some really useful AI systems for robotics and a lot more. So let's jump right in.

---

### Rank 2: MusViT

**Model's Reasoning:** *Fell back to chronological order due to LLM failure.*

**Timestamp:** [51s](https://youtu.be/qtzzN8w2TvU?t=51)

#### Transcript Excerpt:
> First up, we have a really interesting AI called Musev VIT. This is basically an AI model for reading sheet music. Now, this might sound very niche at first, but it's actually a really important missing piece. You see, we already have AI models for images, text, speech, and video, but a page of sheet music isn't just image. It also has info about symbols, timing, pitch, staff lines, spacing, and structure. And a normal vision model doesn't really understand all these relationships properly. So, this is actually a really hard task for an AI model. But Musev VIT is able to take sheet music like this and understand everything. In fact, if you compare Musevit against other vision models, you can see that Musevit is definitely way better in terms of recognizing and classifying sheet music. And the way they trained this is very interesting. They trained it on 9.7 million pages of sheet music covering around 400,000 musical works. And what they did was they actually masked out parts of the original sheet music. So you get something like this. And the AI model during training basically needs to learn how to reconstruct this sheet music from this back into this. And over time from learning how to fill in the missing blanks, it also understands the structure of sheet music and notation and the symbols and how everything works. At the top here, they have released the model to this. So if you click on this link and you scroll down here, it contains all the instructions on how to run this on your computer. Note that this vision model is fairly tiny at less than 500 megabytes in size, so you should be able to run this on most consumer devices. If you're interested in reading further, I'll link to this main page in the description

---

### Rank 3: LongCat 2.0

**Model's Reasoning:** *Fell back to chronological order due to LLM failure.*

**Timestamp:** [153s](https://youtu.be/qtzzN8w2TvU?t=153)

#### Transcript Excerpt:
> below. Also, this week, Chinese food delivery company Muan continues to cook. They just released their latest open-source model, Longat 2.0, and this is a huge deal. What's impressive isn't that they've built a Frontier model that performs very close to the lead enclosed models out there, but it's that they trained this entire model without any Nvidia GPUs. It's important to know that for training AI models, Nvidia GPUs are the gold standard. In fact, it's pretty much impossible or undocumented to train a huge model with any other hardware type. But here it says the full training run and large-scale deployment were built entirely on AI as super pods. Now an ASIC is just a specialized chip in this case for AI. They didn't reveal the brand or the name of these super pods, but there are rumors that these could be Huawei chips. And it's no surprise. I think it's inevitable that China is going to be less reliant on Nvidia chips from the US and instead use their own chips developed domestically for AI training and Huawei could be a major provider of this. What's even more impressive is that here it says their pre-training had no roll backs or irreoverable loss spikes, demonstrating that we have capacity to conduct frontier scale training on alternative hardware platforms. Training huge AI models is actually very unstable. It's not uncommon for the training run to just crash or die due to a loss spike, in which case they would have to roll back to a previous stable version and then keep training again. But here it says that they did not encounter any roll backs or irreversible loss spikes, which is crazy. This signifies that these new specialized AI chips actually run very smoothly for AI training. Anyway, back to the specs of this model. This is a 1.6 trillion parameter model and this is a mixture of experts models. So think of it as like a team of AI agents working together to help you solve the problem. And when you use it, only 48 billion of these 1.6 trillion parameters are activated. So this makes it quite efficient. And like most frontier models out there, this model is also designed for coding agents and long context work. In fact, if you look at these benchmarks, it's extremely impressive, especially for a food delivery company. So in terms of these agentic coding and reasoning benchmarks like terminal bench or sui bench it beats Google's current best model Gemini 3.1 Pro and it's edging pretty close to the top closed models out there including GPT 5.5 and the claude opus models. Now this is completely open source and you can link it with any harness or tool out there like claude code or openclaw open code hermes etc. And you can get it to do a ton of things. For example, here we are linking it to cloud code and getting it to create a PowerPoint presentation. And as you can see, it's able to complete this very well. Or here's an example where we can get it to analyze data. And here we are getting it to code up an entire maze web app. Now, at the top of the page, they've released everything already. So, if you click on this GitHub repo and you scroll down a bit here, it contains all the instructions on how to download and run this locally on your computer. It even works for NPUs and not just GPUs. Everything is released under the MIT license which is very permissive. Now, if you go on Hugging Face, note that even the FP8 version of Lancat 2 is over 2 TB in size and that's because this is a huge 1.6 trillion parameter model. So, don't expect this to be able to fit on any consumer GPU. You'll need to stack like a ton of enterprise GPUs to run this. However, because this is open weights, I'm sure the community is going to release more quantized versions and unfiltered versions of this in the future, which could potentially fit on consumer devices. For now, if you are interested in reading further, I'll link to this main page in the description

---

### Rank 4: LiveEdit

**Model's Reasoning:** *Fell back to chronological order due to LLM failure.*

**Timestamp:** [380s](https://youtu.be/qtzzN8w2TvU?t=380)

#### Transcript Excerpt:
> below. Also, this week, we have liveedit. As the name implies, this can edit videos in real time, allowing users to make changes to the video as it's playing. So, here are some examples for your reference. This just takes any reference video plus a prompt with instructions on how you want to edit the video and it'll pull this off in real time. Here it says it can edit videos at a speed of almost 13 frames per second. And as you can see from these examples, it's very versatile. You can do a ton of things from replacing clothing to changing the weather, removing objects, or changing the style and composition of certain objects. The key here is that it adapts a regular video model into a causal chunk-wise streaming setup, which means it can process frames in small chunks instead of needing the whole video at once. And that's how you can essentially just stream a video into it and get it to edit it in real time. Now, at the top of the page, they have released a code button to this. And if you scroll down a bit here, it contains all the instructions on how to download and run this locally on your computer. Plus, they also released the training script as well. Note that the total size of everything is only 17 GB, so it's fairly small. This can fit on mid to high-end GPUs. If you're interested in reading further, I'll link to this main page in the description below. Also,

---

### Rank 5: VidiHand

**Model's Reasoning:** *Fell back to chronological order due to LLM failure.*

**Timestamp:** [457s](https://youtu.be/qtzzN8w2TvU?t=457)

#### Transcript Excerpt:
> this week, we have Vidi Hand. This is a program that can reconstruct 3D hand movements from videos. So, here are some examples. It can figure out the exact position and shape of a person's hand in 3D space just by looking at a video of the hand. Now, this is actually really hard to do for existing AI models, and that's because hands move really quickly. They often olude each other, or they're oluded by objects, so you can't really see parts of the hand, and small errors are very noticeable. A lot of hand tracking systems can get the overall shape, but they're not very precise. It's not able to accurately capture the exact positions of the fingers, but here, Vidi Hand is able to generate this a lot more accurately, even if parts of the hand are not in view. And if you look at all these hand detection benchmarks, then you can see that Vidy Hand outco competes other competitors across all these metrics. Here are some qualitative comparisons for your reference between Vidy Hand and the other competitors. And as you can see, Videand is a lot more accurate and coherent. And this tool actually matters a lot, especially for training humanoid robots. You see, hands are one of the most important parts of human interaction. And if we can reconstruct this data accurately, then we can create better training data for robotics as well as for augmented or virtual reality. Now, at the top of the page, they have released a code button. And here it says the code will be released soon. So stay tuned for that. If you're interested in reading further, I'll link to this main page in the description

---

## Draft Post (Paste from LLM here):

*(Your draft post goes here)*
