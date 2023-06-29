package sk.tuke.gamestudio.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import sk.tuke.gamestudio.entity.Rating;
import sk.tuke.gamestudio.entity.Score;
import sk.tuke.gamestudio.game.core.Game;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

@Service
public class RatingServiceRestClient implements RatingService{

    private final String url = "http://localhost:8080/api/rating";
    @Autowired
    private RestTemplate restTemplate;
    @Override
    public void setRating(Rating rating) throws RatingException {
        restTemplate.postForEntity(url,rating,Rating.class);
    }

    @Override
    public int getAverageRating(String game) throws RatingException {
//        ResponseEntity<Rating> response = restTemplate.getForEntity(url, Rating.class);
//        Rating rating = response.getBody();
//        if (rating == null) {
//            throw new RatingException("Could not get rating for game: " + game);
//        }
        return getAverageRating(game);
    }

    @Override
    public int getRating(String game, String player) throws RatingException {
        ResponseEntity<Rating> response = restTemplate.getForEntity(url + "/rating/{game}/{player}", Rating.class, game, player);
        if (response.getStatusCode() == HttpStatus.OK) {
            Rating rating = response.getBody();
            if (rating != null) {
                return getRating(game,player);
            }
        }
        throw new RatingException("Failed to get rating for game " + game + " and player " + player);
    }

    @Override
    public List<Rating> getRatings(String game) throws RatingException {
        return Arrays.asList(restTemplate.getForEntity(url + "/" + game, Rating[].class).getBody());
    }

    @Override
    public void reset() throws RatingException {
        throw new UnsupportedOperationException("Not supported via web service");
    }
}
