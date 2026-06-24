package sk.tuke.gamestudio.service;


import sk.tuke.gamestudio.entity.Rating;

import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.transaction.Transactional;
import java.util.List;


public class RatingServiceJPA implements RatingService {

    @PersistenceContext
    private EntityManager entityManager;

    @Transactional
    @Override
    public void setRating(Rating rating) throws RatingException {
        var ratings = entityManager.createNamedQuery("Rating.checkRating")
                .setParameter("game", rating.getGame()).setParameter("player", rating.getPlayer()).setMaxResults(1).getResultList();
        if (ratings.isEmpty())
            entityManager.persist(rating);
        else {
            Rating userRating = (Rating) ratings.get(0);
            userRating.setRating(rating.getRating());

        }
        //entityManager.persist(rating);
    }


    @Override
    public int getAverageRating(String game) throws RatingException {
        return entityManager.createQuery("SELECT AVG(r.rating) FROM Rating r WHERE r.game=:game")
                .setParameter("game", game).getParameters().size();//getsingle
    }

    @Override
    public int getRating(String game, String player) throws RatingException {
        return  entityManager.createQuery("SELECT r FROM Rating r WHERE r.game=:game ORDER BY r.rating DESC")
                .setParameter("game",game)
                .getFirstResult();
    }

    @Override
    public List<Rating> getRatings(String game) throws RatingException {
        return entityManager.createQuery("SELECT s FROM Rating s WHERE s.game=:game")
                .setParameter("game", game).setMaxResults(10).getResultList();
    }

    @Override
    public void reset() {
         entityManager.createNativeQuery("delete from rating").executeUpdate();

    }
}
