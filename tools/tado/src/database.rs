use rusqlite::{Connection,Result};
use chrono::{NaiveDate};
use crate::types::tado::{Tado};

pub fn init(db: &Connection) -> Result<()>{
    db.execute(
        "CREATE TABLE IF NOT EXISTS todos(
            id      INT,
            title   TEXT NOT NULL,
            is_done BOOL,
            date    TEXT NOT NULL
        )",
        (),
    )?;
    Ok(())
}

pub fn new_id(db: &Connection) -> Result<u32>{
    let raw_id: Option<u32> = db.query_row(
        "SELECT MAX(id) FROM todos",
        [],
        |row| row.get(0),
    )?;
    if let Some(last_id) = raw_id {
        Ok(last_id+1)
    } else {
        Ok(1)
    }
}

pub fn save(item: &Tado, db: &Connection) -> Result<()>{
    db.execute(
        "INSERT INTO todos (id, title, is_done, date) VALUES (?1,?2,?3,?4)",
        (&item.id, &item.title, &item.is_done, &item.date)
    )?;
    Ok(())
}

pub fn remove(item: &Tado, db: &Connection) -> Result<()>{
    db.execute(
        "DELETE FROM todos WHERE id = ?1",
        [&item.id]
    )?;
    Ok(())
}

pub fn mark_done(item: &Tado, db: &Connection) -> Result<()>{
    db.execute(
        "UPDATE todos SET is_done = true WHERE id = ?1",
        [&item.id]
    )?;
    Ok(())
}
pub fn get_todo_by_date(db: &Connection, date: &NaiveDate) -> Result<Vec<Tado>>{
    let mut raw_db_content = db.prepare("SELECT id, title, is_done, date FROM todos WHERE date=?1")?;
    let iter = raw_db_content.query_map([date], |row| {
        Ok(Tado {
            id: row.get(0)?,
            title: row.get(1)?,
            is_done: row.get(2)?,
            date: row.get(3)?,
        })
    })?;
    let mut result: Vec<Tado> = Vec::new();
    for item in iter{
        result.push(item.unwrap());
    }
    Ok(result)
}
