const path = require("path");
const BundleTracker = require("webpack-bundle-tracker");

module.exports = (env, argv) => {
    const isProduction = argv.mode === "production";

    return {
        mode: argv.mode,

        entry: "./src/index.js",

        output: {
            path: path.resolve(__dirname, "./static/frontend"),

            filename: isProduction ? "[name].[contenthash].js" : "[name].js",

            assetModuleFilename: isProduction
                ? "assets/[name].[contenthash][ext]"
                : "assets/[name][ext]",

            clean: true,
        },

        devtool: isProduction ? false : "eval-source-map",

        module: {
            rules: [
                {
                    test: /\.m?js$/,
                    exclude: /node_modules/,
                    use: {
                        loader: "babel-loader",
                    },
                },

                {
                    test: /\.(png|jpe?g|gif|svg|webp)$/i,
                    type: "asset/resource",
                },
            ],
        },

        optimization: {
            minimize: isProduction,

            splitChunks: {
                chunks: "all",
            },

            runtimeChunk: "single",

            moduleIds: "deterministic",
        },

        cache: {
            type: "filesystem",
        },

        performance: {
            hints: isProduction ? "warning" : false,
        },

        plugins: [
            new BundleTracker({
                path: path.resolve(__dirname, "./static/frontend"),
                filename: "webpack-stats.json",
            }),
        ],

        resolve: {
            extensions: [".js", ".jsx", ".mjs"],
        },
    };
};
