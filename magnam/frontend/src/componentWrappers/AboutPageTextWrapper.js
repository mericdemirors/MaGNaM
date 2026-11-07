import React from "react";
import { useTheme } from "../context/ThemeContext";
import {
    FaYoutube,
    FaInstagram,
    FaDiscord,
    FaGithub,
    FaEnvelope,
} from "react-icons/fa"; // FontAwesome examples

const ClickableLink = ({ url, theme }) => {
    // Defensive check to ensure url exists
    if (!url) return null;

    return (
        <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            style={{ ...theme.styles.linkText }}
        >
            {url}
        </a>
    );
};

export function AboutPageTextWrapperTR() {
    const { theme } = useTheme();
    const b = theme.styles.baseText;
    const t = theme.styles.titleText;
    const s = theme.styles.subtitleText;
    const d = theme.styles.descriptionText;
    const m = theme.styles.metadataText;
    const l = theme.styles.linkText;
    const i = { ...l, fontSize: theme.typography.fontSize.xl };
    const sh = { boxShadow: theme.colors.shadow.card };
    return (
        <div
            style={{
                paddingInline: theme.spacing.xl,
            }}
        >
            {/* ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> MaGNaM nedir?</p>
                <p style={d}>
                    MaGNaM, her türlü Anime ve Manga içeriğini bir araya
                    getirmeyi ve harmanlamayı amaçlayan bir içerik paylaşım
                    platformudur. Ana ve öncelikli hedefimiz, Türk içerik
                    üreticilerinin ilk eserlerini sergileyebilecekleri ve daha
                    geniş kitlelere ulaşabilecekleri ortak, tanınmış bir
                    platform oluşturmaktır.
                </p>

                <p style={d}>
                    Şu anda Türk medyasında, özellikle anime, manga ve benzeri
                    içeriklerde gördüğümüz en büyük sorun, içerik üreticilerinin
                    orijinal eserlerini geniş kitlelere sergileyememesidir.
                    Elbette bazı platformlar ve küçük çaplı topluluklar var,
                    ancak bu alternatifler küçük ölçekli içerik üreticilerine
                    hizmet etmiyor. Büyük ve zaten başarılı bir içerik üreticisi
                    olsanız bile, eserlerinizi Türk tüketicisine
                    duyurabileceğiniz bir platform yok. Ya kendi takipçi
                    kitlenizle sınırlısınız ya da eserlerinizi duyurmak için
                    büyük bir web sitesine/geniş erişimli medyaya ihtiyacınız
                    var.
                </p>
            </div>
            {/* GOALS ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}>
                    {" "}
                    MaGNaM'ın ulaşmak istediği hedefler şu şekilde
                    sıralanabilir:
                </p>
                <ul style={d}>
                    <li>
                        Hem içerik üreticilerini hem de tüketicileri barındıran,
                        her Türk tüketicisinin her Türk içeriğini bulabileceği
                        büyük bir platform olmak.
                    </li>
                    <li>
                        Sponsorlardan ve tüketicilerden gelen paranın içerik
                        üreticilerine ödendiği, kendi kendini idame ettiren bir
                        ekosistem olmak. Medya üretimini sadece bir hobi
                        olmaktan çıkarıp daha ciddi bir 'iş' haline getirmek
                        için desteklemek.
                    </li>
                    <li>
                        Türk orijinal eserlerini içeren MaGNaM dergisini
                        yayinlamak. Bunu aylık olarak yayınlamayı çok isterdik,
                        ancak şu anki aylık içerik miktarıyla mevsimlik
                        olacağını düşünüyoruz.
                    </li>
                    <li>
                        MaGNaM'ın kapsamını manga odaklı olmaktan anime, ürünler
                        vb. diğer alanlara genişletmek.
                    </li>
                    <li>
                        Anime ve Manga söz konusu olduğunda "Türkiye'nin
                        Markası" olmak.
                    </li>
                </ul>
            </div>
            {/* WHY USE IT ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> Neden MaGNaM kullanmalıyım?</p>
                <p style={s}>İçerik Üreticileri:</p>
                <ul style={d}>
                    <li>
                        İçerik üretmek istiyorum ama bazı ortaklara ihtiyacım
                        var
                    </li>
                    <li>
                        Zaten biraz içerik üretiyorum ve genel Türkçe kitleye
                        açılmak istiyorum
                    </li>
                </ul>

                <p style={s}>İçerik Tüketicileri:</p>
                <ul style={d}>
                    <li>
                        Türkçe çeviriler bulmak istiyorum ama her şüpheli siteye
                        bakmaktan bıktım
                    </li>
                    <li>
                        Türkiye'deki son Anime ve Manga durumundan haberdar
                        olmak istiyorum
                    </li>
                </ul>
            </div>
            {/* HOW TO USE IT ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> MaGNaM nasıl kullanılır?</p>
                <p style={b}> Bu bölümü alt bölümlere ayırabiliriz:</p>
                <p style={s}>Haberler</p>
                <p style={d}>
                    Haberler sayfasında bazı önemli duyurular yapacağız. Belki
                    MaGNaM ile ilgili bazı şeyler veya büyük iş
                    birlikleri/sponsorluklar vb. Eğer gerçekten
                    ilgilenmiyorsanız bunları görmezden gelebilirsiniz.
                    Haberler, sahip olduğumuz diğer tüm kanallardan daha çok
                    topluluğa ulaşmak için kullanılacak bir kanal olacak.
                    Haberlerle ilgili en önemli şeyin korumak istediğimiz
                    şeffaflık olduğunu düşünüyoruz. Kullanıcıları ilgilendiren
                    MaGNaM ile ilgili herhangi bir karar haberler aracılığıyla
                    duyurulacak, ancak daha da önemlisi, kullanıcı yorumlarını
                    toplamak için aylık anketler düzenlemeyi planlıyoruz. Bu,
                    düzenli bir kullanıcının bizimle iletişime geçmesi ve
                    düşüncelerini ifade etmesi için en büyük fırsat olacak.
                </p>
                <p style={s}>Manga</p>
                <p style={d}>
                    Manga alanında manga arayabilir, oluşturabilir ve
                    okuyabilirsiniz. Bu alan, okunmaya hazır içerikleri
                    barındırmak için tasarlanmıştır. Orijinal içerik veya başka
                    bir kaynaktan çevrilmiş/taranmış olması fark etmez.
                    Tamamlanmış ve cilalanmış her şey kabul edilir.
                </p>
                <p style={s}>Portföy (Yetenek avı)</p>
                <p style={d}>
                    Portföy alanında her türlü çalışmanızı (çizimler, videolar,
                    ses kayıtları, kısa çizgi romanlar/mangalar)
                    sergileyebilirsiniz. Bu alan, çalışmalarınızı saklamak veya
                    ilerlemenizi göstermek için DEĞİLDİR (en azından temiz ve
                    aranabilir bir alan olarak kalmasını tercih ediyoruz.
                    Paylaşmaya değer bulduğunuz her şeyi paylaşmaktan
                    çekinmeyin, ancak daha fazla portföy = bulut sunucusunda
                    daha fazla depolama alanı ihtiyacı = daha pahalı hizmet =
                    bakımı daha zor anlamına geldiğini unutmayın. Yani
                    "çalışmalarınızı saklamak" ve "ilerlemenizi göstermek"
                    derken, bunun çok sayıda portföy oluşturup "100 günden 1.
                    gün, her gün mangamın 1 karesini çiziyorum" tarzı
                    yolculuklarınızı belgelemek için bir alan OLMADIĞINI
                    kastediyoruz. Bu alanın, çizer/yazar arkadaşı bulma
                    platformu olmasını istiyoruz. Bir sanatçı manga fikrini
                    çizecek bir hikaye anlatıcısı bulmak istiyorsa, bir yazar
                    karakterlerini çizecek illüstratörlere ihtiyaç duyuyorsa
                    veya bir anime stüdyosu seslendirme sanatçısı arıyorsa vb.
                    İnsanların aradıkları becerileri bulmak için portföyleri
                    filtreleyip aramalarını istiyoruz.
                </p>
                <p style={s}>Profil</p>
                <p style={d}>
                    Profil alanında diğer kullanıcılarla etkileşim kurabilir,
                    hesabınıza para yükleyebilir, tüm içeriklerinize kolayca
                    erişebilir ve belki de MaGNaM'ı kendi zevkinize göre biraz
                    özelleştirebilirsiniz (web sitesi tasarımını tamamen
                    özelleştirilebilir ve bu özelleştirmeleri paylaşılabilir
                    hale getirmeyi umuyoruz).
                </p>
                <p style={s}>Yarışmalar</p>
                <p style={d}>
                    Yarışma bölümünde bazı yarışmalar düzenleyeceğiz. Bu bölüm
                    daha çok yeni serileri, konseptleri ve MaGNaM'ı tanıtmak
                    için. Sadece güzel içeriklere bakmak için burada bulunan
                    sıradan kullanıcılar bu sayfayı görmezden gelebilirler.
                </p>
                <p style={s}>Kanban Görevleri</p>
                <p style={d}>
                    Bu sayfanın alt kısmındaki Kanban bölümünde, kullanıcılar
                    tarafından gönderilen istekler arasından hangi
                    iyileştirmeleri yapacağımızı seçiyoruz. Bu bölümün içerikle
                    hiçbir ilgisi yoktur. Sadece topluluğun geliştiricilerden
                    bir şeyler talep edebileceği bir kanal içindir. Bir hata
                    bulduysanız veya aklınızda bir fikir varsa, bize ulaşmak
                    için en iyi kanal burasıdır. Lütfen aşırıya kaçmayın.
                </p>
            </div>
            {/* FUTURE ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> MaGNaM'a ne olacak</p>
                <p style={d}>
                    MaGNaM'ı geliştirmeye devam edeceğiz ve talep görürsek mobil
                    uygulama geliştirmeye başlayacağız. Muhtemelen ilk bir yıl
                    boyunca kullanıcı geri bildirimleriyle sürekli geliştirme
                    aşamasında kalmayı bekliyoruz. MaGNaM'ın kendi kendine yeten
                    bir ekosistem olduğundan emin olduktan sonra, anime ve ürün
                    medyasıyla daha büyük adımlar atacağız. O noktada birkaç
                    küçük anime stüdyosu ve ürün yaratıcısının olmasını
                    bekliyoruz. Resmi MaGNaM anime stüdyosu ve ürünlerini bizim
                    desteğimizle oluşturmak için iş birliği talebinde
                    bulunacağız.
                </p>

                {/* SECURITY ------------------------------------------------- */}

                <p style={t}> MaGNaM kullanmak güvenli mi?</p>
                <p style={d}>Evet. Topluluğumuzdan sadece 3 şey istiyoruz:</p>
                <p style={s}>1-ŞİFRELERİNİZİ GÜVENDE TUTUN</p>
                <p style={d}>
                    Elbette verilerinizin güvenliğini sağlamak bizim
                    sorumluluğumuzda. MaGNaM'daki girişleri ve diğer tüm veri
                    transferlerini (ödemeler dahil) kontrol ediyoruz ve en
                    güvenli seçeneklerle çalışmak için elimizden gelenin en
                    iyisini yapıyoruz. Elbette her zaman daha güvenli olabilir,
                    ancak bir noktadan sonra her şey kendi şifrelerinizi
                    korumanıza bağlıdır. İki faktörlü kimlik doğrulama (2FA)
                    uygulamasına yönelik çok sayıda talep alırsak, bunu
                    yapacağız. Unutmayın ki biz Google, Amazon veya
                    MasterCard/Visa/Paypal değiliz; bankalarla, Google
                    hesaplarınızla ve bulut sunucu sağlayıcımızın temel
                    kodlarıyla doğrudan etkileşime giremiyoruz, bu nedenle
                    dünyadaki herkes gibi onlara güveniyoruz. Herhangi bir
                    rahatsızlığa neden olmamak için elimizden gelenin en iyisini
                    yapacağız.
                </p>
                <p style={s}>
                    2-MÜMKÜN OLDUĞUNCA KENDİ GOOGLE E-POSTALARINIZI KULLANIN
                </p>
                <p style={d}>
                    Unutmayın ki profil e-postaları, MaGNaM kimliğinizi
                    tanımlayan tek bilgi parçasıdır. Kimliklerinizi taklitçilere
                    karşı korumanıza izin veriyoruz. Diyelim ki Ahmet ve Betül
                    diye iki kişi var. Ahmet, betül@gmail.com ile bir MaGNaM
                    profili oluşturuyor; Biz Ahmet'in, Betül gibi davranmasına
                    izin vermemeliyiz, bu nedenle Betül'un betül@gmail.com
                    e-posta'lı Google hesabını kullanarak giriş yapması
                    durumunda hesabı devralmasına izin veriyoruz. Hesabınızın
                    başkaları tarafından ele geçirilmesini önlemek için lütfen
                    kontrolünüz altında olan bir e-posta adresi kullanın.
                    Kayıt/giriş/doğrulama işlemlerini daha ayrıntılı olarak
                    nasıl ele aldığımız aşağıda açıklanmıştır:
                </p>
                <p>
                    {" "}
                    {ClickableLink({
                        url: "https://github.com/mericdemirors/MaGNaM/blob/main/designs_and_plans/ProfileVerificationSchemas.pdf",
                        theme: theme,
                    })}{" "}
                </p>
                <p style={s}>3-LÜTFEN HİÇBİR ŞEKİLDE SPAM YAPMAYIN</p>
                <p style={d}>
                    Bu web sitesi, onu bozmanın farklı yollarını bulmanız için
                    DEĞİLDİR. MaGNaM'ın büyük bir şey olmadığını ve savunmasız
                    olduğunu aklınızda tutarak buna göre hareket etmenizi
                    bekliyoruz. MaGNaM herkesin kullanımına açıktır; eğer
                    gerçekten sorun gidermek veya web sitesini bozup
                    bozamayacağınızı görmek için oynamak istiyorsanız: lütfen
                    nazikçe sorun. Diğer kullanıcıları rahatsız etmeden, amaçlı
                    ve gözetim altında yapıldığında herhangi bir sorun
                    görmüyoruz.
                </p>
                <p style={m}>
                    Ve proje kodunu açık kaynak olarak tutuyoruz, böylece altta
                    yatan yapıyı kendiniz kontrol edebilirsiniz.
                </p>
            </div>
            {/* OTHER CONTENTS ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> Diğer MaGNaM'ları nerede bulabilirsiniz?</p>

                <FaDiscord style={i} />
                <a
                    href="https://discord.gg/Z3s2WYv6QG"
                    style={l}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    discord
                </a>

                <FaYoutube style={i} />
                <a
                    href="https://www.youtube.com/@studiomagnam"
                    style={l}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    youtube
                </a>

                <FaInstagram style={i} />
                <a
                    href="https://www.instagram.com/studiomagnam/"
                    style={l}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    instagram
                </a>

                <FaGithub style={i} />
                <a
                    href="https://github.com/mericdemirors/MaGNaM"
                    style={l}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    github
                </a>
            </div>
            {/* FAQ ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> MaGNaM'a sorular</p>
                <p style={d}>
                    Aynı sorulardan çok sayıda aldığımızda bu bölümü
                    dolduracağız. Şimdilik her şeyin oldukça kolay ve anlaşılır
                    olduğunu düşünüyoruz, bu nedenle açıklama gerektirebilecek
                    veya muhtemelen çok sorulacak herhangi bir konumuz yok.
                </p>
                <p style={s}>- MaGNaM ismi nereden geliyor?</p>
                <p style={d}>
                    + İlk defa planlarımı yaparken koyacak bir isme ihtiyacım
                    vardı. O zamanlar aklımda bir isim yoktu ve kısa bir isim
                    gerekiyordu ve her şeyin başlangıcında ana odağı Türk
                    yaratıcılar için "shonen jump benzeri" bir dergi olacak bir
                    platform oluşturmayı planlıyordum. Bu yüzden "dergi
                    (magazine)" ve "isim (name)" kelimelerinden bir kısaltma
                    oluşturdum ve geçici olarak "magnam" yazdım, sonra da
                    arkadaşımla aramızdaki bir espriye benzer şekilde harfleri
                    büyük harfle yazarak "MaGNaM"ı elde ettim. İsmin içinde
                    "manga" veya "anime" ile ilgili hiçbir bağlam yok, bu da
                    biraz komik (en azından bana göre :)).
                </p>
            </div>
            {/* WHO ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> MaGNaM kimdir?</p>
                <p style={d}>
                    İşte önemli katkılarda bulunan ve adlarının geçmesine izin
                    veren kişiler:
                </p>
                <p style={s}>1- Kurucu: </p>
                <p style={d}>
                    Meriç (yani ben) asıl kişi. İşin %95-99'unu tek başına
                    yaptı. Yani bir şey çalışmıyorsa onun suçudur. Ayrıca
                    YouTube videolarında gördüğünüz kişi de o.
                </p>
            </div>
            {/* SPECIAL THANKS TO ------------------------------------------------- */}
            <p style={{ ...s, textAlign: "center" }}>
                {" "}
                Bilerek veya bilmeyerek yardımı geçen ve teşekkürü veya söz
                edilmeyi hak eden kişiler kurumlar (veya lisanlı ürün kullanma
                sonucu sitede belirtmemiz gereken şeyler)
            </p>
            <p style={m}>
                Aslında sitenin ana fontu olarak 'AnimeAce' kullanacaktık ancak
                büyük ve küçük harf farkının olmaması yüzünde başka bir
                'manga-benzeri' font arayışında 'CCWildWordsLower Regular'
                fontunu kullanmaya karar verdik Türkçe karakterleri
                desteklemesinden ötürü. Bu yüzden de bunu belirtmek zorundayız:
                <a href="http://www.onlinewebfonts.com">Web Fonts</a> tarafından
                yapılan fontlar CC BY 4.0 ile lisanslanmıştır.
            </p>
            <p style={m}>
                MaGNaM için Gizlilik Politikası ve Hizmet Şartları belgelerini
                yazma sürecinde, https://github.com/Automattic/legalmattic
                adresinden alıntı gerektiren açık kaynaklı şablonları kullandık.
            </p>
        </div>
    );
}

export function AboutPageTextWrapperEN() {
    const { theme } = useTheme();
    const b = theme.styles.baseText;
    const t = theme.styles.titleText;
    const s = theme.styles.subtitleText;
    const d = theme.styles.descriptionText;
    const m = theme.styles.metadataText;
    const l = theme.styles.linkText;
    const i = { ...l, fontSize: theme.typography.fontSize.xl };
    const sh = { boxShadow: theme.colors.shadow.card };
    return (
        <div
            style={{
                paddingInline: theme.spacing.xl,
            }}
        >
            {/* ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> What is MaGNaM?</p>
                <p style={d}>
                    MaGNaM is a content sharing platform that aims to merge and
                    mix all sorts of Anime & Manga revolving contents. Our main
                    and most prioritized goal is to create a common, well-known
                    platform where Turkish creators can debut and reach out to
                    bigger crowds.
                </p>

                <p style={d}>
                    Currently the biggest problem we see in the Turkish media,
                    around the Anime & Manga and similar contents, is creators
                    not being able to display their original works to masses.
                    Sure there are some platforms and small scoped communities
                    but these alternatives don't serve to small creators. And
                    even if you are a big, already achieved creator there is no
                    platform for you to announce your works to the Turkish
                    consumers. You are either limited to your own community of
                    followers or you require some big website/wide-reach media
                    to announce your work.
                </p>
            </div>
            {/* GOALS ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}>
                    {" "}
                    What MaGNaM wants to achieve can be listed like this:
                </p>
                <ul style={d}>
                    <li>
                        Create one big platform (that hosts both the creators
                        and consumers) where every Turkish consumer can find
                        every Turkish content
                    </li>
                    <li>
                        Create a self-sustaining ecosystem where the money
                        in-flow from sponsors and the consumers are paid to the
                        creators. Support the media creation to shift it to a
                        more serious 'work' rather than just a hobby
                    </li>
                    <li>
                        Publish MaGNaM magazine that contains the Turkish
                        original works. We'd love to publish this monthly but
                        right now with the amount of monthly content we think
                        it'll be seasonally.
                    </li>
                    <li>
                        Enlargen the scope of MaGNaM from manga focused to other
                        fields like anime, merch etc.
                    </li>
                    <li>
                        Be the "Brand of Turkey" when it comes to Anime & Manga.
                    </li>
                </ul>
            </div>
            {/* WHY USE IT ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> Why should I use MaGNaM?</p>
                <p style={s}>Creators:</p>
                <ul style={d}>
                    <li>I want to create content but need some partners</li>
                    <li>
                        I already do some content creation and want to open up
                        to general Turkish
                    </li>
                </ul>

                <p style={s}>Consumer community:</p>
                <ul style={d}>
                    <li>
                        I want to find Turkish translations but tired of looking
                        every sketchy website
                    </li>
                    <li>
                        I want to be aware of recent Anime & Manga state in
                        Turkey
                    </li>
                </ul>
            </div>
            {/* HOW TO USE IT ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> How to use MaGNaM?</p>
                <p style={b}>We can split this part into sub sections:</p>
                <p style={s}>News</p>
                <p style={d}>
                    In the news page we'll announce some big things. Maybe some
                    stuff related to MaGNaM or some big collab/sponsors etc. You
                    can ignore these if you don't really care. News will be used
                    as a channel to reach the community over any other channel
                    we have. We think the most important thing about the news
                    would be the transparency we want to maintain. Any
                    MaGNaM-related decision that is user-concerning will be
                    announced via news, but more importantly we're planning to
                    hold monthly surveys to collect user reviews. That is the
                    biggest chance of a regular user to get in contact with us
                    and express their thoughts.
                </p>
                <p style={s}>Manga</p>
                <p style={d}>
                    In the manga space you can search, create, and read mangas.
                    This space is meant to host the ready-to-read content.
                    Original content or trans/scanlated from another source
                    doesn't matter. Anything finished and polished.
                </p>
                <p style={s}>Portfolio (Skill Hunt)</p>
                <p style={d}>
                    In the portfolio space you can display your works of any
                    kind (drawings, videos, audios, short comics/mangas). This
                    space is NOT for storing your works or displaying your
                    progress (at least we prefer if it stays somewhat a clean
                    searcheable space. Feel free to share anything you find
                    worthy to share but keep in mind that more portfolios = more
                    storage needed in the cloud server = more expensive service
                    = harder to maintain. So when we say "storing your works"
                    and "displaying your progress" we mean that this is NOT a
                    space for you to create lots of portfolios and document your
                    "Day 1 out of 100, drawing 1 panel of my manga each day"
                    type of journeys). What we want this space to be is a
                    penfriend/writerfriend finding platform. If an artist wants
                    to find a story teller to write their manga idea, or if a
                    writer needs some illustrators to draw their characters, or
                    an anime studio looking for voice actors etc. We want people
                    to filter and search portfolios to find what/who's skills
                    they are looking for.
                </p>
                <p style={s}>Profile</p>
                <p style={d}>
                    In the profile space you can interact with other users, top
                    up your account, have an easy access to all your contents,
                    maybe customize MaGNaM to your liking a bit (we hope to make
                    the webside design fully customizable, and these
                    customizations sharable).
                </p>
                <p style={s}>Competitions</p>
                <p style={d}>
                    In the competition space we'll hold some competitions. This
                    part is mostly to hype up the new series, concepts, and
                    MaGNaM itself. Regular user can ignore this page if they are
                    just here to look at some pretty content.
                </p>
                <p style={s}>Kanban Tasks</p>
                <p style={d}>
                    In the kanban section (bottom side of this page) we select
                    which improvements to bring among the user submitted
                    requests. This section is not related to the contents in any
                    way. It's just for community to have a channel to
                    demand/request stuff from the developers. If you have found
                    a bug, or if you have an idea in your mind; this is the best
                    channel to reach out to us. Please dont overuse it.
                </p>
            </div>
            {/* FUTURE ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> What will happen to MaGNaM?</p>
                <p style={d}>
                    We'll continue to improve MaGNaM and start a mobile app
                    development if we see the demand. Probably for the first
                    year or so we are expecting to stay in constant development
                    with the user feedbacks. After we are sure that MaGNaM is a
                    self-sustaining ecosystem, we'll go bigger with the anime
                    and merch medias. At that point we expect to have few small
                    anime studios and merch creators. We'll reach and ask for
                    collab to create official MaGNaM anime studio and merch with
                    our support.
                </p>
            </div>
            {/* SECURITY ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> Is it safe to use MaGNaM?</p>
                <p style={d}>
                    Yes. We only ask for 3 things from our community:
                </p>
                <p style={s}>1-KEEP YOUR PASSWORDS SAFE</p>
                <p style={d}>
                    Of course it's our responsibility to keep your data safe. We
                    control the logins and any other data-transfer in MaGNaM
                    (including the payments) and we do our best to work with the
                    most secure options. Of course it can always be more secure
                    but after a point everything comes down to you protecting
                    your own passwords. If we receive lots of demands towards
                    implementing a two factor authantication (2FA), we'll do
                    that. Keep in mind that we are not Google, Amazon, or
                    MasterCard/Visa/Paypal whatever; we canNOT directly interact
                    with banks, your google accounts, and our cloud server
                    provider's underlying codes so we rely on them as everyone
                    one earth does. We'll try our best to not cause any
                    inconvenince.
                </p>
                <p style={s}>2-USE YOUR OWN GOOGLE E-MAILS WHEN POSSIBLE</p>
                <p style={d}>
                    Dont forget that the profile e-mails are the only piece of
                    information that defines your MaGNaM identity. We protect
                    your 'identities' against the impersonators. For example We
                    have Alice and Bob. Alice creates a MaGNaM profile with
                    bob@gmail.com; We don't allow Alice to act as she is Bob, so
                    we allow Bob to take over the account if he logs in using
                    his google account with bob@gmail.com. To prevent anyone
                    from taking your account, please use a e-mail which you have
                    the control over. Here are how we handle
                    registers/logins/verifications in more depth:
                </p>
                <p>
                    {" "}
                    {ClickableLink({
                        url: "https://github.com/mericdemirors/MaGNaM/blob/main/designs_and_plans/ProfileVerificationSchemas.pdf",
                        theme: theme,
                    })}{" "}
                </p>
                <p style={s}>3-PLEASE DONT SPAM ANYTHING IN ANYWAY</p>
                <p style={d}>
                    This website is NOT for you to find different ways to break
                    it. We expect you to act accordingly keeping in mind that
                    MaGNaM is not a big thing and is vulnerable. MaGNaM is for
                    everyone's use, if you really want to troubleshoot or play
                    around the website to see if you can break it: ask it
                    nicely. We don't see any problem when it's done without
                    disturbing other users, with a purpose and under
                    surveillance.
                </p>
                <p style={m}>
                    And we keep the project code opensource so you can check any
                    underlying structure yourself.
                </p>
            </div>
            {/* OTHER CONTENTS ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> Where to find other MaGNaMs?</p>

                <FaDiscord style={i} />
                <a
                    href="https://discord.gg/Z3s2WYv6QG"
                    style={l}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    discord
                </a>

                <FaYoutube style={i} />
                <a
                    href="https://www.youtube.com/@studiomagnam"
                    style={l}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    youtube
                </a>

                <FaInstagram style={i} />
                <a
                    href="https://www.instagram.com/studiomagnam/"
                    style={l}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    instagram
                </a>

                <FaGithub style={i} />
                <a
                    href="https://github.com/mericdemirors/MaGNaM"
                    style={l}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    github
                </a>
            </div>

            {/* FAQ ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> Questions to MaGNaM</p>
                <p style={d}>
                    We'll fill this part when we receive lots of the same
                    questions. For now we think that everything is fairly easy
                    and understandable so we don't have any concept in our mind
                    that may need some explanations or any questions that'll
                    probably be asked a lot
                </p>
                <p style={s}>- Where does the name MaGNaM come from?</p>
                <p style={d}>
                    + When I was writing my plan, I needed a name to put in the
                    document. At that time I didn't have a name in my mind and I
                    needed that name to be short. Initially I was planning to
                    create a platform that's main focus is to be a 'shonen
                    jump-like' magazine for the Turkish creators. So I created
                    an abbreviation from words "magazine" and "name" as a
                    placeholder "magnam" then capitalized the letters in a way
                    similar to an inside joke I have with my friend to get the
                    "MaGNaM". There's really no context of "manga" or "anime" in
                    the name which is a bit funny (at least to to me:))
                </p>
            </div>

            {/* WHO ------------------------------------------------- */}
            <div style={sh}>
                <p style={t}> Who are MaGNaM?</p>
                <p style={d}>
                    this truly is our MaGNaM! Buuuut, here are people who
                    contributed significantly and agreed to be mentioned:
                </p>
                <p style={s}>1- Founder: </p>
                <p style={d}>
                    Meriç is the main guy. He (that's me btw) did 95-99% of the
                    work by himself. He's also the guy you see in the Youtube
                    videos.
                </p>
            </div>

            {/* SPECIAL THANKS TO ------------------------------------------------- */}

            <p style={{ ...s, textAlign: "center" }}>
                {" "}
                Individuals and organizations who knowingly or unknowingly
                provided assistance and who deserve thanks or mention (or things
                we need to mention on the website as a result of using licensed
                products)
            </p>
            <p style={m}>
                We were originally going to use 'AnimeAce' as the main font for
                the site, but due to the lack of case sensitivity, we decided to
                use 'CCWildWordsLower Regular' instead, as it supports Turkish
                characters, while searching for another 'manga-like' font.
                Therefore, we have to mention this: Fonts made from{" "}
                <a href="http://www.onlinewebfonts.com">Web Fonts</a> is
                licensed by CC BY 4.0
            </p>
            <p style={m}>
                In the process of writing the Privacy Policy and Terms of
                Service documents for MaGNaM, we used the opensourced templates
                from https://github.com/Automattic/legalmattic which requires a
                citation.
            </p>
        </div>
    );
}
