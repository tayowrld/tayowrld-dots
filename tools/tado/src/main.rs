// TADO: Simple TODO cli
// Made by Ivan Kurbakov. 2026-10-20 till now

use rusqlite::{Connection};
use chrono::{NaiveDate, Utc};
use std::{error::Error, path::PathBuf};
use clap::{Parser,CommandFactory};

mod todo;
use todo::parse_date;

mod database;

mod types;
use types::cli::{Action, Cli};
use types::tado::{App, Tado};

mod output;
use output::print_todo_by_date;

fn add_todo_by_date(id: &u32, title: String, date: NaiveDate, db: &Connection) {
    let item = Tado {
        id: *id,
        title,
        is_done: false,
        date,
    };
    let _ = database::save(&item, db);
}

fn app_refresh(
    app: &mut App, 
    db: &Connection, 
    date: &NaiveDate
) -> Result<(), Box<dyn Error>>{
    app.todo = database::get_todo_by_date(db, date)?;
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>>{
    clap_complete::CompleteEnv::with_factory(Cli::command).complete();
    let cli = Cli::parse();

    let home_dir = std::env::var("HOME")?;
    let db = Connection::open(PathBuf::from(home_dir).join(".tado.db"))?;
    let mut tado_app = App {
        todo: Vec::new(),
    };

    let _ = database::init(&db);
    let date = parse_date(cli.date.unwrap_or_else(||Utc::now().date_naive().to_string()));
    let _ = app_refresh(&mut tado_app, &db, &date);

    match cli.action {
        Action::List => {
            print_todo_by_date(
                date,
                &tado_app.todo
            );
        },
        Action::Add { title } => {
            let new_id = database::new_id(&db)?;
            add_todo_by_date(
                &new_id,
                title, 
                date,
                &db
            );
            let _ = app_refresh(&mut tado_app, &db, &date);
            print_todo_by_date(
                date,
                &tado_app.todo
            );
        },
        Action::Done { index } => {
            let item: &Tado = &tado_app.todo[index-1];
            let _ = database::mark_done(
                item, 
                &db, 
            );
            let _ = app_refresh(&mut tado_app, &db, &date);
            print_todo_by_date(
                date,
                &tado_app.todo
            );
        },
        Action::Remove { index } => {
            let item = &tado_app.todo[index-1];
            let _ = database::remove(item, &db);
            let _ = app_refresh(&mut tado_app, &db, &date);
            print_todo_by_date(
                date,
                &tado_app.todo
            );
        },
    }

    Ok(())
}
