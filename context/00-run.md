How to Run

   1. Configuration:
       * Open ai-news-curator/config.yaml.
       * Replace the placeholder channel_id with the actual YouTube channel ID you want to monitor.
       * If you want to use the gemini backend for ranking, set the GEMINI_API_KEY environment variable with your API
         key.

   2. Dependencies:
       * The conda environment ai-news-curator has been created with all the necessary dependencies.

   3. Running the Pipeline:
       * To run the pipeline for new videos from the RSS feed, you can run the following command from the project root
         directory (/Users/amiteshpatel/Desktop/ML/AI_News_Auto):
   1         conda run -n ai-news-curator python ai-news-curator/main.py
       * To process a single video, use the --video-url flag:
   1         conda run -n ai-news-curator python ai-news-curator/main.py --video-url <YOUTUBE_VIDEO_URL>
       * Use the --dry-run flag to run the pipeline without updating the state.json file, which is useful for testing.

  Ranking Backend

   * The application is configured to use the ollama backend by default. For the ranking to work, you need to have the
     Ollama server running locally at http://localhost:11434.
   * If the ranking backend fails, the application will fall back to taking the top N stories in chronological order.

  Scheduling with Cron

  To run the pipeline automatically every hour, you can set up a cron job.

   1. Open your crontab editor:

   1     crontab -e
   2. Add the following line to the file, making sure to replace /path/to/your/conda and
      /Users/amiteshpatel/Desktop/ML/AI_News_Auto with the correct absolute paths if they differ:

   1     0 * * * * /Users/amiteshpatel/miniconda3/envs/ai-news-curator/bin/python /Users/amiteshpatel/Desktop
     /ML/AI_News_Auto/ai-news-curator/main.py >> /Users/amiteshpatel/Desktop/ML/AI_News_Auto/ai-news-curator
     /logs/cron.log 2>&1
      You can find the exact path to your conda environment by running conda info --envs.

  This completes the implementation of the MVP.
