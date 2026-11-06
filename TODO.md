## General TODOs

- [ ] 3- A YouTube series called "How to PROPERLY do ..." which is just a video series where I do some anime/manga related work side to side with pros. Animators show me how to animate and I do it, translators show me how to translate a manga and I do it etc...

- [ ] 4- YouTube series called "let's create a manga from scratch" where it go through all the steps one by one and draw mangas in series


# USER EXPERIENCE SURVEY AFTER GOING PROD

- [ ] 1- User surverys: "Turkish translation?", "Any new tag requests?"

- [ ] 2- Public gelir gider'leri aylık olarak news olarak paylaş. Ne kadar para geldi, ne kadarı nereye gitti hangi manga ne kadar kazandı falan

- [ ] 3- Anime/Manga sequel'i veya OVA'sı çizme competition'u, Her çizerin bir sayfa çizeceği bir manga competitionu, Scamlation (manga editing for comedy) competition, website assets drawing competition, scam voice acting (one minute anime scene sound \[both sound effects and dialogs\] editing) competition. Maybe do something with 'https://setteidreams.net/settei/' website it looks good, competition to send the winner to a global competition. competition with comiPO and https://min-chi.material.jp

- [ ] 4- discord icin emoji ve cikartma gif vs yapma competition'u

- [ ] 4- https://www.instagram.com/badinkstudios?igsh=eXB0c2E1MjRkYmg5

- [ ] 4- ask to users if there is any other missing feature that they want like negative tag filtering "anything besides this tag" sort of thing?

- [ ] 5- do you want like/follow buttons under the show...homepage gallery cards

- [ ] 6- is there anything you want to change?

- [ ] 7- mesaj silme veya P2P sifreleme istiyor musunuz?

- [ ] 8- hangi sort ve filtreleri kaldiralim gereksizler var mi

- [ ] 9- do you want to see the profile pictures in the mesaging panel multiple selection?

- [ ] 9- do you want the custom theme to be local (device&browser-wise) or do you want it to be stored in the db so its user-wise and its applied no matter which device you use?

- [ ] 10- do you think that a user should be able to see the content (manga/portfolio) of another profile they blocked or are blokced by

- [ ] 11- do you want your selected sort/filter tags to be highlighted (in the portfolio/manga/competition homepage highlight the metadata X if X is in the selected tags or selected sortings)

- [ ] 12- Do you want to be able to write inline comments or PDF postit notes on the pages, which can be displayed (or disabled by choice) by the other users

- [ ] 12- Do you want the heptagon manga pointing system instead of \[-100, 100\] range rating?

- [ ] 14- do you want something like reddit karma points

- [ ] 14- do you want descrition/bio fields in the profile?

- [ ] 14- do you want double paged reading?

- [ ] 15- what do you think about the bookmark use? I say it should be hand placed but do you want it to be autoamtically placed when you progress in a manga?

- [ ] 15- do you want page counter like 8/22 at the bottom of the manga viewer additional to the progress bar?

- [ ] 16- custom manga pdf format with audios. Audio can be set up as a passive theme audio to play through the episode or it can be a single play audio that's triggered with something

- [ ] 8- do you want 'reset password button' next to reset verification? If so I need to and add nginx request limit on that endpoint and then also update the privacy policy and terms of service


# OPTIMIZE AFTER GOING PROD

-[ ] 0 do I need to download the PDF to tmp and then parse to send the images back to R2, cant I just keep the PDF im the file system and skip this downloading to the tmp and parse it directly locally and then send it? Would it tire the server? Is it even an important optimization to go after?

-[ ] 1 Create some global unit test base cases. Currently all basetestcase class have the same setup and teradown. Also there are some common classes like Portfolio/Manga/Kanban tags, Portfolio/Manga comments etc. Functionalize common unittests if there are some with more than 4-5 duplicate copies across namespaces, maybe add a global counter as a test wrapper to print "-> test_.... (5 out of 17) Namespace = 6.1s"

-[ ] 2 functionalize the batch population classes and create one big class

-[ ] 2 change the email sending utilities to work with celery async instead of making them work sync and make user wait while its happening

-[ ] 3 does it lag? Check with a profiler to optimize the network payload size. Maybe it is a bit slow in the ReadMangaPage and MangaViewerWrapper. Toggling the cover pages on and off makes the paged mode twitch for a moment

-[ ] 4- maybe use useRef instead of useState in some pages. Below pages can be laggy because they dont use local states but use a state passed from the parent page (which may cause full re-render of the parent page in the case of a update in child component wrapper)
    DateSliderWrapper
    IntegerSliderWrapper
    SwitchWrapper
    TextInputWrapper
    MultipleChoiceSelectionWrapper
    ControlPanelWrapper (because of MultipleChoiceSelectionWrapper)

-[ ] 5- we need unittests to confirm PfPDF2 believes the spoofed metadata, those tests are currently commented out

- [ ] 7- what about frontend build asset size warnings? 

-[ ] 6- create the docker from (MaGNaM/designs_and_plans/dev_to_prop_plan_llm_seed_prompt.txt)

-[ ] 6- do we need cloudflare Turnstile and bot check?

- [ ] 10- Start the development as a free website with all prices set to 0
    when it starts to be mainstream add one time top up payments with something easy like Shopier (non verified users are not allowed to put money in) 
        + and do a donation link but explain the difference:  
            - donation = less commision = more money to server maintenance but no magnam coin to you  
            - shopier = more commision = less money to server maintenance but you get magnam coin  
    when money starts to come in regularly switch to PayTR or iyzico with a subscription plan 
        + or do a patreon subscription that links to the magnam accounts via mails which allows patreon subscribers to get monthly magnam coin payment  
    At some point ask if someone wants to make money out of it then look for a way to make that work. 

- [ ] 11- Change the 'SECURE_HSTS_PRELOAD' to True after a long error/crash-free production time
