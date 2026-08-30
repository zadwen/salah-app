Place a short notification sound here named `adhan_beep.wav`
(or point Settings → Sound → Choose Sound File at any .wav/.mp3/.ogg
file elsewhere on disk).

No sound file is bundled here for licensing reasons -- please use a
beep tone or an adhan clip you have rights to.

Playback uses `pygame.mixer`, so all three formats work the same way
and can be stopped mid-playback (Mute / closing a notification banner
cuts the sound off immediately, rather than letting it finish playing
in the background with no way to silence it).
