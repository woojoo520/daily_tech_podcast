from podgen import Podcast, Episode, Media, Person, Category
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel
import feedparser
from pytz import timezone
from uuid import uuid4
from urllib.parse import urlparse
import os
import calendar


class PodAuthor(BaseModel): 
    name: str 
    email: str = ""
 

default_author = PodAuthor(name="woojoo", email="woojoo10@outlook.com")
class PodEpisode(BaseModel): 
    title: str
    authors: list[PodAuthor] = [default_author]
    description: str = ""
    publication_ts: int 
    asset_url: str
    duration: int 
    size: int
    # script_url: str
    # link: str = ""
    
    def get_authors(self) -> list[Person]:
        return [Person(author.name, author.email) for author in self.authors]
    

class RSSHandler:
    def __init__(self, feed_source: str):
        parsed = self._parse_rss(feed_source)
        self.tz = timezone('Asia/Shanghai')
        self.feed_source = feed_source
        self.podcast = self._create_podcast_from_feed(parsed)

    def _parse_rss(self, feed_source: str):
        if not feed_source:
            # read the existing RSS feed
            base_dir = Path(__file__).resolve().parents[2]
            feed_source = os.path.join(base_dir, "soul_power_tech_news.xml")
            if not os.path.exists(feed_source):
                raise FileNotFoundError(f"Please provide a valid RSS feed source or ensure the file exists at {feed_source}")
            parsed = feedparser.parse(feed_source)
        else:
            if self._is_url(feed_source):
                parsed = self._parse_from_url(feed_source)
            else:
                if not os.path.exists(feed_source):
                    raise FileNotFoundError(f"RSS feed file not found: {feed_source}")
                parsed = feedparser.parse(feed_source)
        return parsed
        
    def _is_url(self, source: str) -> bool:
        """ Check if the source is a valid URL."""
        try:
            result = urlparse(source)
            return all([result.scheme, result.netloc]) and result.scheme in ('http', 'https')
        except Exception:
            return False
    
    def _parse_from_url(self, url: str):
        """ Fetch and parse RSS feed from a URL."""
        import requests
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status() 
            return feedparser.parse(response.text)
            
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch RSS from URL {url}: {e}")
        except Exception as e:
            raise Exception(f"Error parsing RSS from URL {url}: {e}")
        
    
    def _create_podcast_from_feed(self, parsed):
        # create a new Podcast object
        try:
            tags = parsed.feed.tags
            category = tags[0]['term']
            podcast = Podcast(
                name=parsed.feed.title,
                description=parsed.feed.description,
                website=parsed.feed.link,
                explicit=(parsed.feed.itunes_explicit == 'yes'),
                authors=[Person(name=default_author.name, email=default_author.email) ],
                image=parsed.feed.image['href'],
                category=Category(category, subcategory=None if len(tags) == 1 else tags[1]['term']),
                language=parsed.feed.language
            )
        except:
            raise ValueError("Missing key variable for initiate a podcast.")
        
        # add existing episodes
        for entry in parsed.entries:
            media_url = entry.enclosures[0].href
            media_type = entry.enclosures[0].type
            media_size = entry.enclosures[0].length
            duration = self._parse_duration(entry.itunes_duration) 
            summary = entry.summary
            # print(f"authors: {authors}")
            # print(f"id: {entry.id}")
            # print(f"summary: {summary}")
            # print(f"title: {entry.title}")
            
            ts = calendar.timegm(entry.published_parsed)  # 转为 UTC timestamp
            utc_dt = datetime.fromtimestamp(ts, tz=timezone('UTC'))  # 安全方式，不用 utcfromtimestamp
            pub_dt = utc_dt.astimezone(self.tz)  # 转为东八区时间

            episode = Episode(
                title=entry.title,
                authors=[default_author],
                summary=summary,
                id=entry.id,
                media=Media(
                    url=media_url, 
                    size=media_size,
                    type=media_type, 
                    duration=timedelta(seconds=duration)),
                publication_date=pub_dt,
            )
            podcast.episodes.append(episode)

        return podcast
    
    def _parse_duration(self, duration_str: str) -> int:
        parts = [int(p) for p in duration_str.strip().split(":")]
        return int(timedelta(
            hours=parts[-3] if len(parts) == 3 else 0,
            minutes=parts[-2] if len(parts) >= 2 else 0,
            seconds=parts[-1]
        ).total_seconds())
    
    def add_new_episodes(self, episode: PodEpisode):
        # add new episodes
        publication_date = datetime.fromtimestamp(episode.publication_ts, self.tz)
        self.podcast.episodes.append(
            Episode(
                title=episode.title,
                authors=[default_author],
                summary=episode.description, 
                id=str(uuid4()),  
                media=Media(
                    episode.asset_url, 
                    type="audio/mpeg", 
                    size=episode.size,
                    duration=timedelta(seconds=episode.duration)
                ),
                publication_date=publication_date
            )
        )

    def get_rss_str(self) -> str:
        # return the RSS feed as a string
        return self.podcast.rss_str()
    
    def export_rss_to_file(self, filepath: str = None):
        # export RSS
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.get_rss_str())


            
if __name__ == "__main__":
    src_filepath = "/Users/woojoo/workspace/daily_tech_podcast/soul_power_tech_news.xml"
    tar_filepath = "/Users/woojoo/workspace/daily_tech_podcast/soul_power_tech_news.xml"
    rss_handler = RSSHandler(feed_source="")
    content = rss_handler.get_rss_str()
    print(f"content: {content}")
    summary= """
    本期 Soul Power Tech News 为你带来最新的科技商业动态，包括：

小米汽车大获成功，苹果却退出造车；特朗普与马斯克决裂，后者组建新党；Apple 因反垄断罚款上诉欧盟；Meta 高薪挖角 OpenAI 四位AI专家；AI模型频现欺骗行为引发安全担忧；OpenAI 暂停生物AI功能以防风险；美国专利制度或迎历史性变革；SanDisk SSD 打破全年最低价；WhatsApp 推出多账号切换与文件扫描器；德国对中国AI公司 DeepSeek 展开合规审查。

欢迎收听
    """
    # rss_handler.add_new_episodes(
    #     PodEpisode(
    #         title="Soul Power Tech News - 2025-07-07",
    #         description=summary,
    #         publication_ts=int(datetime.now().timestamp()),
    #         asset_url="https://raw.githubusercontent.com/woojoo520/daily_tech_podcast/main/episodes/2025-07-07/audio.mp3",
    #         # script_url="https://example.com/script.txt",
    #         duration=307,
    #         size=4913901,
    #         # link="https://example.com/episode"
    #     )
    # )
    # rss_handler.export_rss(filepath=tar_filepath)
    # print(f"RSS feed exported to {tar_filepath}")