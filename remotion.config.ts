import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(95);
Config.setCodec("h264");
Config.setCrf(18);
Config.setScale(1);
// No concurrency limit — let GitHub Actions scale freely
Config.setConcurrency(null);
