package sk.tuke.gamestudio.service;
import org.springframework.stereotype.Service;
import sk.tuke.gamestudio.entity.Score;

import java.util.List;
@Service
public interface ScoreService {
    void addScore(Score score) throws ScoreException;
    List<Score> getTopScores(String game) throws ScoreException;
    void reset() throws ScoreException;
}
