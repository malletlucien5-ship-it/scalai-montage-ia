Features
Use Cases
Workflows & API
Pricing
Blog
Try Auphonic
Login

View Help
Features
Listen to audio examples and learn more about our algorithms.

Noise & Reverb Reduction
Choose whether Auphonic should remove only static or also fast-changing noises and if we should keep or eliminate music.

Crystal-clear audio made easy
Do you want to eliminate any ambient sounds from your audio to get a clean speech file? Or do you just want to get rid of static background noises while keeping the singing bird outside your window on record? With our advanced AI denoising algorithms, you have the choice!

Our classifiers also detect segments containing music or breaths, so you can decide if music is part of the content and should remain in your production or if you want to completely isolate the spoken content and remove all breaths and mouth noises.
For even greater speech intelligibility control, it is possible to separately adjust the amount of noise, reverb or breath reduction to strike the perfect balance between clarity and ambiance.

Read more →

►
Play examples
Intelligent Leveler
Balances levels between speakers, music, and speech – no compressor knowledge required.

Ensures all speakers sound equally loud
The Adaptive Leveler corrects level differences between speakers, between music and speech and applies dynamic range compression to achieve a balanced overall loudness. We use classifiers to carefully process music segments and prevent amplification of unwanted noises.

Based on over five years of training with audio files from our web service, the algorithm keeps learning and adapting to new data every day.
It is most suitable for programs, where dialog or speech is the most prominent content such as podcasts, radio, broadcast, lecture and conference recordings, film and videos, screencasts etc.

Read more →

►
Play examples
Filtering, AutoEQ & BWE
Adds missing and removes unwanted frequencies (De-Esser, De-Plosive, etc.) to create a clear, warm, and pleasant sound.

Perfectly balanced frequencies
Our AutoEQ algorithm automatically analyzes and optimizes the frequency spectrum of voice recordings, removing sibilance (De-Esser) and plosives (De-Plosive) while creating a clear, warm, and pleasant sound.

The equalization of multi-speaker audio can be complex and time-consuming, as each voice requires its own unique frequency spectrum equalization. Our AutoEQ simplifies this process by creating separate, time-dependent EQ profiles for each speaker, ensuring a consistent and pleasant sound output despite any changes in the voices during the recording.

Using our Bandwidth Extension (BWE), you can even recover high frequencies lost in archival or low-bitrate voice recordings, making speech sound brighter and more lifelike.

Read more →

►
Play examples
Cut Filler Words, Coughs and Silence
Automatically cut silent segments, pauses, coughs and filler words like "ah", "uhm", "mh", or "ähm" in multiple languages.

Remove pauses, coughs and fillers in one click
A few seconds of silence quickly arise due to equipment re-adjustment or short speaking pauses to breathe or think. Many speakers also tend to fill the thinking pauses with "ah", "uhm", "mh", etc. to avoid awkward silence.
Whether it is silence, respiratory noises or filler words, listeners usually do not enjoy listening to informationless audio.

Our automatic cutting algorithms reliably detect and remove silent segments, coughs, throat-clearings, sneezes and filler words. Simply enable the algorithms in your production without further settings to cut redundant filler content and achieve a high-quality listening experience. If you want, you can also check, add and edit the cuts manually in our Auphonic Audio Inspector or export the provided cut lists for fine-tuning in your favorite audio/video editor.

Read more →

►
Play examples
Multitrack Algorithms
Process multiple tracks to create an optimized mixdown - featuring automatic ducking, noise gate and mic bleed removal.

More control with multiple tracks
Auphonic multitrack leverages multiple input audio files to produce a balanced, high-quality final mixdown. The algorithm processes individual and combined tracks, including speech tracks from multiple microphones, music tracks, and remote speakers via phone or Skype. This allows for a balanced loudness between tracks, with dynamic range compression applied only to speech segments and automatic ducking of music/FX tracks.
Denoising per track, adaptive noise gates and mic bleed removal decrease noise, bleed and reverb in the final mixdown by identifying when and in which track a speaker is active.

Auphonic's multitrack algorithm produces exceptional results, making it the go-to solution for audio professionals.

Read more →

►
Play examples
Loudness Specifications
Define a target loudness, true peak limit, MaxLRA, and more for consistency across files and compliance with audio specs.

Produce for Netflix, Audible, Podcasts in one click
Auphonic is the perfect tool for you to never again worry about admission criteria for different platforms (Audible, Netflix, Spotify, podcasts, etc.) or broadcasters (EBU R128, ATSC A/85, radio and mobile, commercials).
You can define a set of target parameters (integrated loudness, true peak level, dialog normalization, MaxLRA, MaxM, MaxS), like -16 LUFS for podcasts, and we will produce the audio accordingly in one click.

Read more →

►
Play examples
Speech2Text & Automatic Shownotes
Multilingual speech-to-text with auto-generated shownotes and chapters, displayed in a shareable transcript editor.

Make your audio searchable and accessible
Auphonic uses a multilingual Whisper model by OpenAI as self-hosted speech recognition engine, including a sharable transcript editor that can easily be integrated into your post production workflow without extra costs. In addition to our Whisper engine, we also integrated a wide range of popular external speech recognition services, including Amazon Transcribe, Google Cloud Speech API, wit.ai and Speechmatics.

Our Automatic Shownotes and Chapters feature gives you AI-generated summaries in multiple levels of detail and timestamped thematic sections, that you can use as shownotes and chapters to boost your podcast's accessibility and search engine visibility.
For multitrack productions, each track is processed separately, so you get a detailed transcript showing which speaker is active at what exact time.

Read more →

►
Play examples
Video Support, Metadata & Chapters
Create enhanced audio or video podcasts with chapters and waveform audiograms in all the output formats you need.

All audio and video formats supported
Chapter marks or enhanced podcasts are used for quick navigation within audio files and can be entered directly in our web interface or imported from various sources such as text files or audio editors (DAWs).
Auphonic supports all common audio and video file formats, offers customized encoding settings, maps metadata tags to multiple output files and exports them to platforms such as Soundcloud, YouTube, and Spreaker.

By generating videos from audio files, including a dynamically generated waveform, cover image or chapter images as the background, audiograms allow you to create shareable videos from audio-only productions with ease.

In video productions, Auphonic extracts the audio track, processes and merges it with the original video track without any loss of image quality. You can export the processed video to YouTube or create an audio-only version for your podcast platform automatically.

Read more →

►
Play examples
Try our algorithms with your own audio files!
Get started →
Automated Workflows & API Integrations
Automatic Content Deployment
Publish your results to multiple platforms like YouTube, Libsyn, PodBean, Soundcloud, Facebook automatically and use all common file transfer services to avoid manual up- and downloads.
Watch Folders, Zapier, API & CLI
Watch folders, the Auphonic API & CLI and our Zapier interface allows you to integrate our services into your workflows and applications. Want to integrate your product within Auphonic? We offer external service integrations.
White Label API and Customization
Directly integrate Auphonic into your digital audio workstations, content distribution platforms and other products with custom algorithms and pricing.
Read more about workflows and our API →
POST /api/productions.json
{
"preset": "Podcast Standard" ,
"input_file": "episode12.flac" ,
"action": "start"
}
Frequently Asked Questions

How long can I use Auphonic for free?

Do I get more features with a premium plan?

Does Auphonic integrate with other software and tools?

Is there a developer API available for the software?

How long does it typically take to improve my audio file?
Help →
Blog →
Press →
Footer
Product
Features
Use Cases
Workflows & API
Pricing
Changelog
Resources
Help
Blog
API Docs
Auphonic CLI
Service Status
Company
About
Contact
Jobs
Press
Legal
Imprint
Terms of Service
Privacy Policy
Subscribe to our newsletter
Stay up to date with important updates and news.

Subscribe
Newsletter
Newsletter
Twitter
Mastodon
Facebook
LinkedIn
© 2026 by Auphonic GmbH