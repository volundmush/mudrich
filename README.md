# MudRich - A MUD-focused Monkey-Patch extension for Textualize/rich

## CONTACT INFO
**Name:** Volund

**Email:** volundmush@gmail.com

**PayPal:** volundmush@gmail.com

**Discord:** Volund#1206  

**Discord Channel:** https://discord.gg/Sxuz3QNU8U

**Patreon:** https://www.patreon.com/volund

**Home Repository:** https://github.com/volundmush/mudrich

## TERMS AND CONDITIONS

MIT license. In short: go nuts, but give credit where credit is due.

Please see the included LICENSE.txt for the legalese.

## INTRO
MUDs and their brethren are the precursors to our modern MMORPGs, and are still a blast to play - in addition to their other uses, such as educative game design: all the game logic, none of the graphics!

Writing one from scratch isn't easy though, so this library aims to take away a great deal of the pain involved in handling colored text.

Rich is an excellent ANSI library on its own, but since my proposals to add MXP/Pueblo support to Styles were rejected, and I found other features a little lacking for my purposes, I decided to create this little helper library to monkey-patch in support for those necessary things.


## OKAY, BUT HOW DO I USE IT?
Glad you asked!

You can install MudRich using ```pip install git+git://github.com/volundmush/mudrich```

You can then install the monkey-patches using:
```python
from mudrich import install_mudrich
install_mudrich()
```

You should do this first thing in your program, before importing anything from rich.

There's an included Circle-style and Evennia-style decoder for taking Circle or Evennia markup and turning into Rich.

## FAQ 
  __Q:__ This is cool! How can I help?  
  __A:__ [Patreon](https://www.patreon.com/volund) support is always welcome. If you can code and have cool ideas or bug fixes, feel free to fork, edit, and pull request! Join our [discord](https://discord.gg/Sxuz3QNU8U) to really get cranking away though.

  __Q:__ I found a bug! What do I do?  
  __A:__ Post it on this GitHub's Issues tracker. I'll see what I can do when I have time. ... or you can try to fix it yourself and submit a Pull Request. That's cool too.

## Special Thanks
  * The Evennia Project.
  * The Textualize group behind Rich.
  * All of my Patrons on Patreon.
  * Anyone who contributes to this project or my other ones.
