// COMPETITION
export const COMPETITION_MIN_TITLE_LEN = 1;
export const COMPETITION_MAX_TITLE_LEN = 200;
export const COMPETITION_MIN_DESCRIPTION_LEN = 1;
export const COMPETITION_MAX_DESCRIPTION_LEN = 400;
export const COMPETITION_MIN_LINKS_LEN = 0;
export const COMPETITION_MAX_LINKS_LEN = 8096;
export const COMPETITION_IMAGE_MIN_H = 960;
export const COMPETITION_IMAGE_MIN_W = 540;
export const COMPETITION_IMAGE_MAX_H = 3840;
export const COMPETITION_IMAGE_MAX_W = 2160;
export const COMPETITION_IMAGE_MAX_SIZE = 4 * 1024 * 1024;
export const COMPETITION_MIN_TAG_COUNT = 0;
export const COMPETITION_MAX_TAG_COUNT = 32;

// KANBAN
export const KANBAN_MIN_TAG_COUNT = 1;
export const KANBAN_MAX_TAG_COUNT = 8;
export const KANBAN_MIN_DESCRIPTION_LEN = 1;
export const KANBAN_MAX_DESCRIPTION_LEN = 400;
export const KANBAN_MIN_IMPORTANCE = 0;
export const KANBAN_MAX_IMPORTANCE = 9;

// MANGA
export const MANGA_MIN_TITLE_LEN = 1;
export const MANGA_MAX_TITLE_LEN = 200;
export const MANGA_MIN_DESCRIPTION_LEN = 1;
export const MANGA_MAX_DESCRIPTION_LEN = 400;
export const MANGA_MIN_COLLABORATOR_COUNT = 0;
export const MANGA_MAX_COLLABORATOR_COUNT = 32;
export const MANGA_MIN_RATING = -100;
export const MANGA_MAX_RATING = 100;
export const MANGA_MIN_COMMENT_LEN = 0;
export const MANGA_MAX_COMMENT_LEN = 200;
export const MANGA_IMAGE_MIN_H = 960;
export const MANGA_IMAGE_MIN_W = 540;
export const MANGA_IMAGE_MAX_H = 3840;
export const MANGA_IMAGE_MAX_W = 2160;
export const MANGA_IMAGE_MAX_SIZE = 4 * 1024 * 1024;
export const MANGA_MIN_TAG_COUNT = 1;
export const MANGA_MAX_TAG_COUNT = 32;

export const CHAPTER_MIN_TITLE_LEN = 1;
export const CHAPTER_MAX_TITLE_LEN = 200;
export const CHAPTER_MIN_NO_LEN = 1;
export const CHAPTER_MAX_NO_LEN = 200;
export const CHAPTER_MIN_COLLABORATOR_COUNT = 0;
export const CHAPTER_MAX_COLLABORATOR_COUNT = 32;
export const CHAPTER_PDF_MAX_SIZE = 20 * 1024 * 1024;
export const CHAPTER_PDF_MAX_PAGE = 100;
export const MAX_CHAPTER_COUNT_PER_MANGA = 1000;

// NEWS
export const NEWS_MIN_TITLE_LEN = 1;
export const NEWS_MAX_TITLE_LEN = 200;
export const NEWS_MIN_DESCRIPTION_LEN = 0;
export const NEWS_MAX_DESCRIPTION_LEN = 400;
export const NEWS_MIN_LINKS_LEN = 0;
export const NEWS_MAX_LINKS_LEN = 8096;
export const NEWS_IMAGE_MIN_H = 480;
export const NEWS_IMAGE_MIN_W = 720;
export const NEWS_IMAGE_MAX_H = 2160;
export const NEWS_IMAGE_MAX_W = 3840;
export const NEWS_IMAGE_MAX_SIZE = 5 * 1024 * 1024;

// PORTFOLIO
export const PORTFOLIO_MIN_TITLE_LEN = 1;
export const PORTFOLIO_MAX_TITLE_LEN = 200;
export const PORTFOLIO_MIN_DESCRIPTION_LEN = 1;
export const PORTFOLIO_MAX_DESCRIPTION_LEN = 400;
export const PORTFOLIO_MIN_COMMENT_LEN = 1;
export const PORTFOLIO_MAX_COMMENT_LEN = 200;
export const PORTFOLIO_IMAGE_MIN_H = 540;
export const PORTFOLIO_IMAGE_MIN_W = 360;
export const PORTFOLIO_IMAGE_MAX_H = 3840;
export const PORTFOLIO_IMAGE_MAX_W = 2160;
export const PORTFOLIO_IMAGE_MAX_SIZE = 1 * 1024 * 1024;
export const PORTFOLIO_MIN_TAG_COUNT = 0;
export const PORTFOLIO_MAX_TAG_COUNT = 32;

export const WORK_MIN_TITLE_LEN = 0;
export const WORK_MAX_TITLE_LEN = 200;
export const MAX_WORK_COUNT_PER_PORTFOLIO = 50;
export const WORK_IMAGE_MAX_SIZE = 5 * 1024 * 1024;
export const WORK_IMAGE_MIN_H = 0;
export const WORK_IMAGE_MIN_W = 0;
export const WORK_IMAGE_MAX_H = 0;
export const WORK_IMAGE_MAX_W = 0;
export const WORK_PDF_MAX_SIZE = 25 * 1024 * 1024;
export const WORK_PDF_MAX_PAGE = 50;
export const WORK_VIDEO_MAX_SIZE = 50 * 1024 * 1024;
export const WORK_VIDEO_MIN_H = 240;
export const WORK_VIDEO_MIN_W = 320;
export const WORK_VIDEO_MAX_H = 2160;
export const WORK_VIDEO_MAX_W = 3840;
export const WORK_VIDEO_MAX_DURATION = 120;
export const WORK_AUDIO_MAX_SIZE = 10 * 1024 * 1024;
export const WORK_AUDIO_MAX_DURATION = 300;
// some portfolio work file dimensions/attributes are not constrained
// we keep them here in the globals incase future updates needed
export const WORK_VIDEO_MIN_DURATION = 0;
export const WORK_AUDIO_MIN_DURATION = 0;

// PROFILE
export const PROFILE_MESSAGE_MIN_LEN = 1;
export const PROFILE_MESSAGE_MAX_LEN = 400;
export const PROFILE_MIN_NAME_LEN = 1;
export const PROFILE_MAX_NAME_LEN = 64;
export const PROFILE_MIN_PASSWORD_LEN = 8;
export const PROFILE_MAX_PASSWORD_LEN = 512;
export const PROFILE_MIN_EMAIL_LEN = 1;
export const PROFILE_MAX_EMAIL_LEN = 128;
export const PROFILE_IMAGE_MIN_H = 16;
export const PROFILE_IMAGE_MIN_W = 16;
export const PROFILE_IMAGE_MAX_H = 224;
export const PROFILE_IMAGE_MAX_W = 224;
export const PROFILE_IMAGE_MAX_SIZE = 1 * 1024 * 1024;

// OTHERS
export const GALLERY_FETCH_TIMEOUT_DELAY = 400;
export const HOMEPAGE_MIN_DATE = "2026-01-01";
export const HOMEPAGE_MAX_DATE = "2028-01-01";
export const COMPETITION_HOMEPAGE_PRICE_MAX_RANGE = 100000;
export const COMPETITION_HOMEPAGE_INTEGER_RANGE_MAX = 100;
export const MANGA_HOMEPAGE_INTEGER_RANGE_MAX = 1000;
export const PORTFOLIO_HOMEPAGE_INTEGER_RANGE_MAX = 1000;

export const SPINNERHEIGHT = 40;
export const ALLOWED_PDF_EXTENSIONS = ["pdf"];
export const ALLOWED_VIDEO_EXTENSIONS = ["mp4", "mov", "mkv"];
export const ALLOWED_AUDIO_EXTENSIONS = ["mp3", "wav"];
export const ALLOWED_IMAGE_EXTENSIONS = [
    "png",
    "jpg",
    "jpeg",
    "webp",
    "gif",
    "svg",
];
export const PDF_PAGE_IMAGE_NAME_FORMAT_LEN = 4;
