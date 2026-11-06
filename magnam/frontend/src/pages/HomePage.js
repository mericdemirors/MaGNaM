import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import SEO from "../componentWrappers/SEO";

import CreateNewsPage from "./CreateNewsPage";
import ShowNewsPage from "./ShowNewsPage";
import ShowProfilePage from "./ShowProfilePage";
import AccountPage from "./AccountPage";
import ShowHomePage from "./ShowHomePage";
import ShowPortfolioHomePage from "./ShowPortfolioHomePage";
import CreatePortfolioPage from "./CreatePortfolioPage";
import ShowPortfolioPage from "./ShowPortfolioPage";
import ShowMangaHomePage from "./ShowMangaHomePage";
import CreateMangaPage from "./CreateMangaPage";
import CreateChapterPage from "./CreateChapterPage";
import ShowMangaPage from "./ShowMangaPage";
import ReadMangaPage from "./ReadMangaPage";
import ShowCompetitionHomePage from "./ShowCompetitionHomePage";
import CreateCompetitionPage from "./CreateCompetitionPage";
import ShowCompetitionPage from "./ShowCompetitionPage";
import AboutPage from "./AboutPage";
import VerifyProfilePage from "./VerifyProfilePage";
import CreateThemePage from "./CreateThemePage";

function HomePage() {
    return (
        <Router>
            <SEO />
            <Routes>
                <Route path="/" element={<ShowHomePage />} />
                <Route path="/news/:news_id/" element={<ShowNewsPage />} />
                <Route path="/create-news/" element={<CreateNewsPage />} />

                <Route path="/account/" element={<AccountPage />} />
                <Route
                    path="/profile/:profile_id/"
                    element={<ShowProfilePage />}
                />

                <Route path="/portfolio/" element={<ShowPortfolioHomePage />} />
                <Route
                    path="/portfolio/:portfolio_id/"
                    element={<ShowPortfolioPage />}
                />
                <Route
                    path="/portfolio/create-portfolio/"
                    element={<CreatePortfolioPage />}
                />

                <Route path="/manga/" element={<ShowMangaHomePage />} />
                <Route path="/manga/:manga_id/" element={<ShowMangaPage />} />
                <Route
                    path="/read-manga/:manga_id/:chapter_id?/"
                    element={<ReadMangaPage />}
                />
                <Route
                    path="/manga/create-manga/"
                    element={<CreateMangaPage />}
                />
                <Route
                    path="/manga/create-chapter/:manga_id/"
                    element={<CreateChapterPage />}
                />

                <Route
                    path="/competition/"
                    element={<ShowCompetitionHomePage />}
                />
                <Route
                    path="/competition/:competition_id/"
                    element={<ShowCompetitionPage />}
                />
                <Route
                    path="/competition/create-competition/"
                    element={<CreateCompetitionPage />}
                />

                <Route path="/about/" element={<AboutPage />} />
                <Route path="/verify/:token/" element={<VerifyProfilePage />} />

                <Route path="/theme/" element={<CreateThemePage />} />
            </Routes>
        </Router>
    );
}

export default HomePage;
