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
3. Simulate content of respons.