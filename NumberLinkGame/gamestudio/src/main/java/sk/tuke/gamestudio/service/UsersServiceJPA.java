package sk.tuke.gamestudio.service;


import sk.tuke.gamestudio.entity.Users;

import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.transaction.Transactional;
import java.util.List;

@Transactional
public class UsersServiceJPA implements UsersService {
    @PersistenceContext
    private EntityManager entityManager;

    @Override
    public void addUser(Users users) throws UsersException {
        entityManager.persist(users);
    }

    @Override
    public List<Users> getUsers() throws UsersException {
        return entityManager.createNamedQuery("Users.getUsers").getResultList();
    }
}
