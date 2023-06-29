package sk.tuke.gamestudio.service;


import sk.tuke.gamestudio.entity.Comment;

import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.transaction.Transactional;
import java.util.List;


public class CommentServiceJPA implements CommentService {
    @PersistenceContext
    private EntityManager entityManager;
    @Transactional
    @Override
    public void addComment(Comment comment) throws CommentException {
        entityManager.persist(comment);
    }

    @Override
    public List<Comment> getComments(String game) throws CommentException {
        return entityManager.createQuery("SELECT s FROM Comment s WHERE s.game=:game")
                .setParameter("game", game).setMaxResults(10).getResultList();
    }

    @Override
    public void reset() {
        entityManager.createQuery("DELETE FROM Comment").executeUpdate();
    }
}
