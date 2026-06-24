package sk.tuke.gamestudio.server.webservice;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import sk.tuke.gamestudio.entity.Rating;
import sk.tuke.gamestudio.entity.Score;
import sk.tuke.gamestudio.service.RatingException;
import sk.tuke.gamestudio.service.RatingService;
import sk.tuke.gamestudio.service.ScoreService;

import java.util.List;

@RestController
@RequestMapping("/api/rating")
public class RatingServiceRest {
    @Autowired
    private RatingService ratingService;

    @PostMapping("/{game}")
    public void setRating(@RequestBody Rating rating)  {
        ratingService.setRating(rating);
    }

    @GetMapping("/{game}")
    public List<Rating> getRatings(@PathVariable String game){
        return  ratingService.getRatings(game);
    }

    @GetMapping("/{avarage}/{game}")
    public int getAverageRating(@PathVariable String game) throws RatingException {
        return ratingService.getAverageRating(game);
    }
//    @GetMapping
//    public void reset() {
//        ratingService.reset();
//    }
}