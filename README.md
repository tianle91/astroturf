# astroturf

Given an entity, we want to find all users that comment on that entity.
For each user, we score the sentiments of comments that mention that entity as well as overall sentiment.

We then learn that user's overall commenting pattern and simulate a distinct user independent of that user.
This means learning how and when a user comments.

# sentiment

Problems:
1. Sentiment of comment is not necessarily sentiment towards entity.
2. Hit-rate of entities with common usage is low. E.g. Uber (the company) is not uber (the adjective).

# simulate

To-do:
1. Get all comments by user.
2. Simulate when response occurs.
3. Simulate content of response.

# quotables

https://www.reddit.com/r/Entrepreneur/comments/b328hu/spotting_fake_users/eixl9p6?utm_source=share&utm_medium=web2x

Some example patterns that I found on twitter are...
- bots only posting about a single topic
- bots only posting during specific time frames
- bots constantly replying to #MAGA or @AOC within 1 minute
- bots following everyone that follows @AOC, @realDonaldTrump, etc.
- bots following other bots

# demo

- find and tag entity mentions
- finetune on user who had most positive entity mention
- simulate user response

# technical

Directory structure

```
root or <gs://astroturf-dev/>

data: stuff from scraper
    search: from call to pushshift api
        comment
            q={query}
                {comment_id}.json: comments returned from query
    user: from call to praw (require praw.ini)
        {username}
            {comment_id}.json: user comments and comment context
finetune: stuff for huggingface transformers
    {username}
        data: inputs for model training
            train.txt
            valid.txt
            test.txt
        model: outputs of Trainer()
            ???
```