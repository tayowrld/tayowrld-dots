use chrono::NaiveDate;
use crate::types::tado::Tado;

pub fn print_todo_by_date(date: NaiveDate, todo: &[Tado]) {
    print!("! ");
    print!("{:<32}", " TODO ");
    print!(" STAT ");
    print!(" DATE ");
    print!("\n\n");

    let mut index = 0;

    for item in todo {
        index+=1;
        if item.date == date {
            let mut item_title = item.title.clone();
            if item_title.chars().count() > 30 {
                while item_title.chars().count() > 27{
                    item_title.pop();
                }
                item_title+="...";
            } else {
                let _fill_count = 30 - item_title.chars().count();
            }
            if item.is_done {
                print!("\x1b[9m"); // Strikethrough all "DONE" todos
            }
            print!("{:<2}", index.to_string());
            print!(" \x1b[1m");
            print!("{:<30}", item_title);
            print!(" \x1b[0m");
            if item.is_done {
                print!("\x1b[9m");
            }
            if item.is_done {
                print!("\x1b[32m DONE \x1b[0m");
            }
            else {
                print!("\x1b[33m TODO \x1b[0m");
            }
            if item.is_done {
                print!("\x1b[9m"); // Strikethrough all "DONE" todos
            }
            print!(" ");
            print!("{}", date);
            if item.is_done {
                print!("\x1b[0m");
            }
            print!("\n");
        }
    }
}
