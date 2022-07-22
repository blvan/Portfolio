#include <sstream>
#include <stdio.h>
#include <sys/types.h>
#include <string.h>
#include <libusb-1.0/libusb.h>
#include <array>
#include <conio.h>
#include<stdlib.h>
#include <math.h>
#include <windows.h>
#include <iomanip>
#include <ctime>
#include <dos.h>
#include <cstdio>
#include <regex>
#include <iomanip>
#include <fstream> 
#include <cstring>
#include<iostream>
#include<string>
#include<vector>
#include<map>
#include <thread>
#include <float.h>











typedef std::chrono::high_resolution_clock Clock;
using std::stringstream;
using namespace std;

struct conf {

	char shifr[100]; // шифр Цезаря 
	char deshifr[100];
	char afshifr[100];
	char vizhener[100]; // шифр Виженера 
	char devizhener[100];
	char afvizhener[100];
	char shifr3[100]; // шифр Плейфера 
	char deshifr3[100];
	char afshifr3[100];

};
struct f9 {
	char tns[100];// имя шифра
	float tcs; // время шифровки
	float tcd; // время дешифровки
	int len;



};


void file();
bool ident(conf);
void View();
void Cesar();
void Vizhener();
void Playfair();
void shifr();
void shifr2();
void shifr3();
void key();
void Edit();
void compare();
int key1;
string key2 = "";
string key3 = "";
int poly = 0;
int n(0);

FILE* pfile;
std::ofstream s;


void printdev(libusb_device* dev) {
	int interdesc­;
	int bInterfaceNumber;
	int bNumEndpoints;
	int epdesc­;
	int bDescriptorType;
	int bEndpointAddress;
	libusb_device_descriptor desc;
	const libusb_interface* inter;
	const libusb_interface_descriptor* interdesc;
	const libusb_endpoint_descriptor* epdesc;
	int r = libusb_get_device_descriptor(dev, &desc);
	if (r < 0) {
		fprintf(stderr,
			"Ошибка: дескриптор устройства не получен, код: %d.\n",
			r);
		return;
	}
	
}







int main()
{
	//setlocale(LC_CTYPE, "rus");
	SetConsoleCP(1251);
	SetConsoleOutputCP(1251);

	int a = 0;
	int i = 1;
	system("cls");


tryAgain:

system("cls");

libusb_device** devs; /* указатель на указатель на устройство, */
/* используется для получения списка */
/* устройств */
libusb_context* ctx = NULL; /* контекст сессии libusb */
int r; /* для возвращаемых значений */
ssize_t cnt; /* число найденных USB устройств */
//ssize_t i; /* индексная переменная цикла перебора */
/* всех устройств */
r = libusb_init(&ctx); /* инициализировать библиотеку libusb, */
/* открыть сессию работы с libusb */
if (r < 0) {
	fprintf(stderr,
		"Ошибка: инициализация не выполнена, код: %d.\n", r);
	return 1;
}
libusb_set_debug(ctx, 3); /* задать уровень подробности отладочных */
/* сообщений */
cnt = libusb_get_device_list(ctx, &devs);
/* получить список всех найденных USB */
/* устройств */
if (cnt < 0) {
	fprintf(stderr,
		"Ошибка: список USB устройств не получен.\n", r);
	return 1;
}
system("cls");
printf("======================================\n");
printf("|Будь ласка підключіть флеш-прістрій |\n");
for (i = 0; i < cnt; i++) { /* цикл перебора всех устройств */
	printdev(devs[i]); /* печать параметров устройства */
}
printf("======================================\n");
libusb_free_device_list(devs, 1);
/* освободить память, выделенную */
libusb_exit(ctx);

if (cnt <8) // cnt !=6
{
	Sleep(3000);
	goto tryAgain;
}
else
{
	printf("====================================\n");
	printf("|Флешка успішно підключена         |\n");
	printf("====================================\n");
	Sleep(3000);
	printf("====================================\n");
	printf("|Перевірка на наявність ключа      |\n");
	printf("====================================\n");
	Sleep(3000);
	ifstream fileStream("E:\\numb.txt");
	if (fileStream.fail() ) {
		printf("====================================\n");
		printf("|Ключ №1 не знайдено		   |\n");
		printf("|Підключіть ключ-флешку           |\n");
		printf("====================================\n");
		Sleep(2000);
		system("cls");
		goto tryAgain;

	}
	else
	{
		printf("====================================\n");
		printf("|Ключ №1 знайдений	  	   |\n");
		printf("====================================\n");
		Sleep(2000);
	}
	ifstream fileStream2("E:\\key.txt");
	 if(fileStream2.fail())
	{
		printf("====================================\n");
		printf("|Ключ №2 не знайдено		   |\n");
		printf("|Підключіть ключ-флешку             |\n");
		printf("====================================\n");
		Sleep(2000);
		system("cls");
		goto tryAgain;

	}
	 else
	 {
		 printf("====================================\n");
		 printf("|Ключ №2 знайдений		   |\n");
		 printf("====================================\n");
		 Sleep(2000);
	 }
	ifstream fileStream3("E:\\key2.txt");
	 if (fileStream3.fail())
	{
		printf("====================================\n");
		printf("|Ключ  №3 не знайдено		   |\n");
		printf("|Підключіть ключ-флешку            |\n");
		printf("====================================\n");
		Sleep(2000);
		system("cls");
		goto tryAgain;

	}
	else
	{
		printf("====================================\n");
		printf("|Ключ №3 знайдений		   |\n");
		printf("====================================\n");
		Sleep(2000);
	}

}


if (n == 1)
{
	cout << endl << "Вихід з программи.";	system("pause");
	return 0;
}



while (i != 0)
{
	system("cls");
	cout << endl << "Головне меню:";
	cout << endl << "1:Витяг ключа";
	cout << endl << "2:Шифрування Цезаря";
	cout << endl << "3:Шифрування Виженера";
	cout << endl << "4:Шифрування Плейфера";
	cout << endl << "5:Редагування ключа";
	cout << endl << "6:Показ таблиці";
	cout << endl << "7:Очищення файлу з даними.";
	cout << endl << "0:Вихід з программи.";
	cout << endl << endl << "Виберіть пункт меню:";
	cin.sync();

	cmatch result;
	string vibor;
	bool flag = false;
	do
	{
		cin.sync();
		getline(cin, vibor);
		regex  regular("([0-8]{1})");
		if (regex_match(vibor.c_str(), result, regular))
		{
			flag = true;
		}
		else
		{
			cout << "Введений пункт меню не знайдений." << endl << "Повторіть введення:";
			//system("pause");
		}

	} while (!flag);
	a = stoi(result[0]);

	switch (a)
	{
	case 1: {
		key();
		break;
	}

	case 2: {
		shifr();
		break;
	}
	case 3: {
		shifr2();
		break;
	}
	case 4: {
		shifr3();
		break;
	}
	case 5: {
		Edit();
		break;
	}
	case 6: {

		View();
		break;

	}
	case 7: {
		file();
		break;
	}
	case 0: {
		cout << endl << "Вихід з програми.";	system("pause");
		return 0;
	}


	}

}
}


void key()
{
	system("cls");
	 poly = 2;
	ifstream file("E:\\numb.txt"); //открываем файл для чтения
	do
	{
		file >> key1; //записываем в переменные содержание файла 
	} while (!file.eof());//пока не наступил конец файла
	printf("==============\n");
	cout << "|" << setw(12) << right << key1 << "|\n"; //показываем, что значения успешно перезаписало
	printf("==============\n");
	file.close();

	ifstream jo("E:\\key.txt"); //открываем файл для чтения
	do
	{
		jo >> key2; //записываем в переменные содержание файла 
	} while (!jo.eof());//пока не наступил конец файла
	printf("==============\n");
	cout << "|" << setw(12) << right << key2 << "|\n"; //показываем, что значения успешно перезаписало
	printf("==============\n");
	jo.close();

	ifstream jojo("E:\\key2.txt"); //открываем файл для чтения
	do
	{
		jojo >> key3; //записываем в переменные содержание файла 
	} while (!jojo.eof());//пока не наступил конец файла
	printf("==============\n");
	cout << "|" << setw(12) << right << key3 << "|\n"; //показываем, что значения успешно перезаписало
	printf("==============\n");
	jojo.close();
	system("pause");
}




void shifr()  //шифр цезаря 
{
	system("cls");
	//setlocale(LC_CTYPE, "rus");


	if (poly == 0)
	{
		cout << "Будь ласка витягніть ключ \n";
		system("pause");
		return;
	}
	string s;
	string scear = "Шифр Цезаря";
	f9 tm;
	conf st;
	cmatch result;
	char otv, vybor = 1;
	while (vybor == 1)
	{
		float t = 0;
		bool flag = false;
		cout << "Введить рядок:";
		cmatch result;
		string shirfat;
		bool Trger = false;
		do
		{
			cin.sync();
			getline(cin, shirfat);
			regex  regular("([0-9]{0,999})");
			if (regex_match(shirfat.c_str(), result, regular))
			{
				cout << "" << endl << "Повторіть введення:";
			}
			else
			{
				Trger = true;

				//system("pause");
			}

		} while (!Trger);
		s = string(shirfat);
		strcpy_s(st.shifr, s.c_str()); //s = stoi(result[0]);
		tm.len = strlen(st.shifr);
		strcpy_s(tm.tns, scear.c_str());
		// длина строки ===
		cout << "Шифрування:";

		if (key1 % 33 == 0 || key1 % 26 == 0)
		{
			key1 += 2;
		}
		auto start = chrono::high_resolution_clock::now();
		for (auto& c : s)
		{

			if (c >= 'a' && c <= 'z')
				c = ((c - 'a' + key1) % 26) + 'a';
			else if (c >= 'A' && c <= 'Z')
				c = ((c - 'A' + key1) % 26) + 'A';
			if (c >= 'а' && c <= 'я')
				c = ((c - 'а' + key1) % 33) + 'а';
			else if (c >= 'А' && c <= 'Я')
				c = ((c - 'А' + key1) % 33) + 'А';
			this_thread::sleep_for(chrono::microseconds(100));
		}
		auto end = chrono::high_resolution_clock::now();
		chrono::duration<float> duration1 = end - start;
		/*cout << "Шифрование заняло:" << duration1.count() << endl;*/
		ofstream jozef("E:\\time.txt"); //открываем файл для чтения
		jozef << duration1.count() << endl; //записываем в переменные содержание файла 
		jozef.close();

		ifstream file2("E:\\time.txt"); //открываем файл для чтения
		do
		{
			file2 >> tm.tcs; //записываем в переменные содержание файла 
		} while (!file2.eof());//пока не наступил конец файла
		file2.close();

		ofstream ofs;
		ofs.open("E:/time.txt", std::ofstream::out | std::ofstream::trunc); //очистка файла
		ofs.close();

		cout << s << endl;
		strcpy_s(st.deshifr, s.c_str());


		/*	cout << "Шифровка заняла:" << ((float) cl) / CLOCKS_PER_SEC << endl;

			std::cout << "Шифровка заняла:"
				<< std::chrono::duration_cast<std::chrono::nanoseconds>(t2 - t1).count()
				<< " nanoseconds" << std::endl;


			duration = (clock() - start) / (double)CLOCKS_PER_SEC;*/
			/*cout << "Шифровка заняла: " << duration << '\n';*/

		cout << "Дешифрування:";
		auto start2 = chrono::high_resolution_clock::now();
		for (auto& c : s)
		{
			if (c >= 'a' && c <= 'z')
				c = 'z' - (('z' - c + key1) % 26);
			else if (c >= 'A' && c <= 'Z')
				c = 'Z' - (('Z' - c + key1) % 26);
			if (c >= 'а' && c <= 'я')
				c = 'я' - (('я' - c + key1) % 33);
			else if (c >= 'А' && c <= 'Я')
				c = 'Я' - (('Я' - c + key1) % 33);
			this_thread::sleep_for(chrono::microseconds(100));
		}

		auto end2 = chrono::high_resolution_clock::now();
		chrono::duration<float> duration2 = end2 - start2;
		/*cout << "Дешифрование заняло:" << duration2.count() << endl;*/
		ofstream jo("E:\\time.txt"); //открываем файл для чтения
		jo << duration2.count() << endl; //записываем в переменные содержание файла 
		jo.close();

		ifstream file("E:\\time.txt"); //открываем файл для чтения
		do
		{
			file >> tm.tcd; //записываем в переменные содержание файла 
		} while (!file.eof());//пока не наступил конец файла
		file.close();
		ofstream ofs2;
		ofs2.open("E:/time.txt", std::ofstream::out | std::ofstream::trunc); //очистка файла
		ofs2.close();


		strcpy_s(st.afshifr, s.c_str());
		cout << s << endl;
		/*	int time1 = 0;
			time1 = clock();
			cout << endl << "Для вычисления понадобилось "
				<< time1 << " тиков времени или "
				<< ((float)time1) / CLOCKS_PER_SEC << " секунд.n";*/

		system("pause");
		system("cls");

		ofstream tim("E:/time2.txt", ios::binary | ios::app);
		tim.write((char*)&tm, sizeof(tm));
		tim.close();

		ofstream inf("E:/All.dat", ios::binary | ios::app);
		inf.write((char*)&st, sizeof(st));
		inf.close();
		/*	cl = clock() - cl;*/
		cout << endl << "Продовжуємо? (1-так/0-ні)";
		string vibor;
		flag = false;
		do
		{


			cin.sync();
			getline(cin, vibor);
			regex  regular("([0-1]{1})");
			if (regex_match(vibor.c_str(), result, regular))
			{

				flag = true;
			}
			else
			{
				cout << "Некоректне зачення." << endl << "Повторіть введення:" << endl;

			}

		} while (!flag);
		vybor = stoi(result[0]);

	}
	system("pause");
}



void shifr2() //Шифр Виженера 
{
	system("cls");
	conf st;

	int vybor = 1;
	//Строка - результат
   //string key = ""; //Строка - ключ 

	if (poly == 0)
	{
		cout << "Будь ласка витягніть ключ\n";
		system("pause");
		return;
	}
	char dublicat;   //Формирование таблицы Виженера на алфавите латиницы
	bool flag;

	while (vybor == 1)
	{
		f9 tm;
		string name = "Шифр Віженера";
		string s;
		string result = "";
		string result2 = "";
		string key_on_s = "";
		int x = 0, y = 0; //Координаты нового символа из таблицы Виженера
		int registr = 0; //Регистр символа
		int shift = 0;

		bool triger = false;


		char** tabula_recta = new char* [26]; //Таблица Виженера
		for (int i = 0; i < 26; i++)
			tabula_recta[i] = new char[26];
		string alfabet = "abcdefghijklmnopqrstuvwxyz"; //Алфавит латиницы
													   //Формирование таблицы
		for (int i = 0; i < 26; i++)
			for (int j = 0; j < 26; j++)
			{
				shift = j + i;
				if (shift >= 26) shift = shift % 26;
				tabula_recta[i][j] = alfabet[shift];
			}
	
		strcpy_s(tm.tns, name.c_str());
		cout << "Введіть рядок:";
		cmatch math;
		string shifrat;
		bool Trger = false;
		do
		{
			cin.sync();
			getline(cin, shifrat);
			regex  regular("([A-Za-z]{0,999})");
			if (regex_match(shifrat.c_str(), math, regular))
			{
				Trger = true;
			}
			else
			{
				cout << "" << endl << "Повторіть введення:";
				//system("pause");
			}

		} while (!Trger);
		s = string(shifrat);
		strcpy_s(st.vizhener, shifrat.c_str());
		tm.len = strlen(st.vizhener);
		//Формирование строки, длиной шифруемой, состоящей из повторений ключа
		for (int i = 0; i < s.length(); i++)
		{
			key_on_s += key2[i % key2.length()];
		}
		//Шифрование при помощи таблицы
		auto start = chrono::high_resolution_clock::now();
		for (int i = 0; i < s.length(); i++)
		{
			//Если нешифруемый символ
			if (((int)(s[i]) < 65) || ((int)(s[i]) > 122))
				result += s[i];
			else
			{
				//Поиск в первом столбце строки, начинающейся с символа ключа
				int l = 0;
				flag = false;
				//Пока не найден символ
				while ((l < 26) && (flag == false))
				{
					//Если символ найден
					if (key_on_s[i] == tabula_recta[l][0])
					{
						//Запоминаем в х номер строки
						x = l;
						flag = true;
					}
					l++;
				}
				//Уменьшаем временно регистр прописной буквы
				if (((int)(s[i]) <= 90) && ((int)(s[i]) >= 65))
				{
					dublicat = (char)((int)(s[i]) + 32);
					registr = 1;
				}
				else
				{
					registr = 0;
					dublicat = s[i];
				}
				l = 0;
				flag = false;
				//Пока не найден столбец в первой строке с символом строки
				while ((l < 26) && (flag == false))
				{
					if (dublicat == tabula_recta[0][l])
					{
						//Запоминаем номер столбца
						y = l;
						flag = true;
					}
					l++;
				}
				//Увеличиваем регистр буквы до прописной
				if (registr == 1)
				{
					//Изменяем символ на первоначальный регистр
					dublicat = char((int)(tabula_recta[x][y]) - 32);
					result += dublicat;
				}
				else
					result += tabula_recta[x][y];
			}
			this_thread::sleep_for(chrono::microseconds(100));
		}
		auto end = chrono::high_resolution_clock::now();
		
		chrono::duration<float> duration1 = end - start;
		/*cout << "Шифрование заняло:" << duration1.count() << endl;*/
		ofstream jozef("E:\\time.txt"); //открываем файл для чтения
		jozef << duration1.count() << endl; //записываем в переменные содержание файла 
		jozef.close();

		ifstream file2("E:\\time.txt"); //открываем файл для чтения
		do
		{
			file2 >> tm.tcs; //записываем в переменные содержание файла 
		} while (!file2.eof());//пока не наступил конец файла
		file2.close();

		ofstream ofs;
		ofs.open("E:/time.txt", std::ofstream::out | std::ofstream::trunc); //очистка файла
		ofs.close();


		cout << "Шифрування:";
		cout << result << endl;
		strcpy_s(st.devizhener, result.c_str());
		
		s = result;
		
		 //Формирование строки, длиной дешифруемой, состоящей из повторений ключа
		for (int i = 0; i < result.length(); i++)
		{
			key_on_s += key2[i % key2.length()];
		}
		//Дешифрование при помощи таблицы
		auto start2 = chrono::high_resolution_clock::now();
		for (int i = 0; i < result.length(); i++)
		{
			//Если недешифруемый символ
			if (((int)(result[i]) < 65) || ((int)(result[i]) > 122))
				result2 += result[i];
			else
			{
				//Поиск в первом столбце строки, начинающейся с символа ключа
				int l = 0;
				flag = false;
				//Пока не найден символ
				while ((l < 26) && (flag == false))
				{
					//Если символ найден
					if (key_on_s[i] == tabula_recta[l][0])
					{
						//Запоминаем в х номер строки
						x = l;
						flag = true;
					}
					l++;
				}
				//Уменьшаем временно регистр прописной буквы
				if (((int)(result[i]) <= 90) && ((int)(result[i]) >= 65))
				{
					dublicat = (char)((int)(result[i]) + 32);
					registr = 1;
				}
				else
				{
					registr = 0;
					dublicat = s[i];
				}
				l = 0;
				flag = false;
				//Пока не найден столбец в x строке с символом строки
				while ((l < 26) && (flag == false))
				{
					if (dublicat == tabula_recta[x][l])
					{
						//Запоминаем номер столбца
						y = l;
						flag = true;
					}
					l++;
				}
				//Увеличиваем регистр буквы до прописной
				if (registr == 1)
				{
					//Изменяем символ на первоначальный регистр
					dublicat = char((int)(tabula_recta[0][y]) - 32);
					result2 += dublicat;
				}
				else
					result2 += tabula_recta[0][y];
			
			}
			this_thread::sleep_for(chrono::microseconds(100));
		}
		auto end2 = chrono::high_resolution_clock::now();
		chrono::duration<float> duration2 = end2 - start2;
	/*	cout << "Де-шифрование заняло:" << duration2.count() << endl;*/
		ofstream jojo("E:\\time.txt"); //открываем файл для чтения
		jojo << duration2.count() << endl; //записываем в переменные содержание файла 
		jojo.close();
		ifstream file("E:\\time.txt"); //открываем файл для чтения
		do
		{
			file >> tm.tcd; //записываем в переменные содержание файла 
		} while (!file.eof());//пока не наступил конец файла
		file.close();

		ofstream ofc;
		ofc.open("E:/time.txt", std::ofstream::out | std::ofstream::trunc); //очистка файла
		ofc.close();






		cout << "Дешифрування:" << result2 <<endl; //Вывод результата
		strcpy_s(st.afvizhener, result2.c_str());

		system("pause");
		system("cls");
		ofstream tim("E:/time2.txt", ios::binary | ios::app);
		tim.write((char*)&tm, sizeof(tm));
		tim.close();

		ofstream inf("E:/All2.dat", ios::binary | ios::app);
		inf.write((char*)&st, sizeof(st));
		inf.close();

		cout << endl << "Продовжуємо? (1-так/0-ні)";
		cmatch math2;
		string vibor;
		triger = false;
		do
		{


			cin.sync();
			getline(cin, vibor);
			regex  regular("([0-1]{1})");
			if (regex_match(vibor.c_str(), math2, regular))
			{

				triger = true;
			}
			else
			{
				cout << "Некоректне зачення." << endl << "Повторіть введення:" << endl;

			}

		} while (!triger);
		vybor = stoi(math2[0]);

	}
	system("pause");
}







void shifr3() // шифр Плейфера 
{
	system("cls");
	conf st;
	f9 tm;
	string name = "Шифр Плейфера";
	const int N = 100;
	char letters[26] = "ABCDEFGHIKLMNOPQRSTUVWXYZ";//Used to fill the matrix
	int flag[25] = { 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 };
	//Mark whether the letter is already in the matrix, corresponding to the letters array
	char ch[5][5];//5X5 matrix
	char ch1[N];//Key
	char ch2[N];//ciphertext
	int len = 'a' - 'A';
	int flg = 1;
	int i, j, k, n;
	int vybor = 1;
	strcpy_s(ch1, key3.c_str());
	if (poly == 0)
	{
		cout << "Будь ласка витягніть ключ\n";
		system("pause");
		return;
	}



	while (vybor == 1)
	{




		for (int i = 0; i < strlen(ch1); i++)//Convert the entered key into uppercase letters
		{
			ch1[i] = ch1[i] - len;
		}
		for (int i = 0; i < strlen(ch1); i++)//change all J in the key to I        
		{
			if (ch1[i] == 'J')ch1[i] = 'I';
		}
		int i = 0; int j = 0;
		//Fill the letter in the key into the matrix and mark the letter as used
		for (int k = 0; k < strlen(ch1); k++)
		{
			for (int t = 0; t < 25; t++)
			{
				if (ch1[k] == letters[t] && flag[t] == 0)
				{
					ch[i][j] = letters[t];
					flag[t] = 1;
					if (j < 4)j++;
					else { i++; j = 0; }
				}
			}
		}
		for (int k = 0; k < 25; k++)//Fill the unused letters into the matrix in alphabetical order
		{
			if (flag[k] == 0)
			{
				ch[i][j] = letters[k];
				flag[k] = 1;
				if (j < 4)j++;
				else { i++; j = 0; }
			}
		}
		cout << "Матриця після заповнення ключа: " << endl;
		for (i = 0; i < 5; i++)
			for (j = 0; j < 5; j++)
			{
				cout << ch[i][j];
				cout << " ";
				if (j == 4)
					cout << endl;
			}

		/////////////////////Matrix generation completed////////////////////////// //
		

		string ans = "";
		cout << "Введіть рядок:";
		string s, origin;
		cmatch math;
		string shifrat;
		bool Trger = false;
		do
		{
			cin.sync();
			getline(cin, shifrat);
			int l = shifrat.size();
			/*cout << l;*/
			regex  regular("([a-z]{0,999})");
			if (regex_match(shifrat.c_str(), math, regular) /*|| l > 10 || l < 5*/)
			{ 
				regex  regular("([А-Яа-я]{0,999})");
				if (regex_match(shifrat.c_str(), math, regular) /*|| l > 10 || l < 5*/)
				{
					cout << "" << endl << "Повторіть введення:";
				}
				else{
					Trger = true;
				}

			}
			else
			{

				cout << "" << endl << "Повторіть введення:";
				

				//system("pause");
			}



		} while (!Trger);
		origin = string(shifrat);

		strcpy_s(tm.tns, name.c_str());
		/*getline(cin, origin);*/
		//cout << key3 << endl;


		for (i = 0; i < origin.size(); i++) {
			if (origin[i] != ' ')
				s += origin[i];
		}
		strcpy_s(st.shifr3, s.c_str());
		tm.len = strlen(st.shifr3);
		n = 5;
		vector<vector<char> > a(5, vector<char>(5, ' '));

		map<char, int> mp;
		k = 0;
		int pi, pj;
		for (i = 0; i < n; i++) {
			for (j = 0; j < n; j++) {
				while (mp[key3[k]] > 0 && k < key3.size()) {
					k++;
				}
				if (k < key3.size()) {
					a[i][j] = key3[k];
					mp[key3[k]]++;
					pi = i;
					pj = j;
				}
				if (k == key3.size())
					break;
			}
			if (k == key3.size())
				break;
		}
		k = 0;
		for (; i < n; i++) {
			for (; j < n; j++) {
				while (mp[char(k + 'a')] > 0 && k < 26) {
					k++;
				}
				if (char(k + 'a') == 'j') {
					j--;
					k++;
					continue;
				}
				if (k < 26) {
					a[i][j] = char(k + 'a');
					mp[char(k + 'a')]++;
				}
			}
			j = 0;
		}

		if (s.size() % 2 == 1)
			s += "x";
		for (i = 0; i < s.size() - 1; i++) {
			if (s[i] == s[i + 1])
				s[i + 1] = 'x';
		}
		map<char, pair<int, int> > mp2;
		for (i = 0; i < n; i++) {
			for (j = 0; j < n; j++) {
				mp2[a[i][j]] = make_pair(i, j);
			}
		}
		auto start = chrono::high_resolution_clock::now();
		for (i = 0; i < s.size() - 1; i += 2) {
			int y1 = mp2[s[i]].first;
			int x1 = mp2[s[i]].second;
			int y2 = mp2[s[i + 1]].first;
			int x2 = mp2[s[i + 1]].second;
			if (y1 == y2) {
				ans += a[y1][(x1 + 1) % 5];
				ans += a[y1][(x2 + 1) % 5];
			}
			else if (x1 == x2) {
				ans += a[(y1 + 1) % 5][x1];
				ans += a[(y2 + 1) % 5][x2];
			}
			else {
				ans += a[y1][x2];
				ans += a[y2][x1];
			}
			this_thread::sleep_for(chrono::microseconds(100));
		}
		auto end = chrono::high_resolution_clock::now();
		chrono::duration<float> duration1 = end - start;
		/*cout << "Шифрование заняло:" << duration1.count() << endl;*/
		ofstream jojo("E:\\time.txt"); //открываем файл для чтения
		jojo << duration1.count() << endl; //записываем в переменные содержание файла 
		jojo.close();
		ifstream file("E:\\time.txt"); //открываем файл для чтения
		do
		{
			file >> tm.tcs; //записываем в переменные содержание файла 
		} while (!file.eof());//пока не наступил конец файла
		file.close();

		ofstream ofc;
		ofc.open("E:/time.txt", std::ofstream::out | std::ofstream::trunc); //очистка файла
		ofc.close();

		cout << "Шифрування:" << ans << '\n';
		strcpy_s(st.deshifr3, ans.c_str());
		s = ans;

		int f = 0;
		/*do {*/
			strcpy_s(ch2, ans.c_str());
			for (int k = 0; k < strlen(ch2); k++)//Convert the entered ciphertext into uppercase letters
			{
				if (ch2[k] >= 'a')
					ch2[k] = ch2[k] - len;
			}
			for (int k = 0; k < strlen(ch2); k++)//change all J in the ciphertext to I
			{
				if (ch2[k] == 'j')ch2[k] = 'i';
			}
			
				//Decryption begins
				auto start2 = chrono::high_resolution_clock::now();
				for (int k = 0; k < strlen(ch2); k += 2)
				{
					int m1, m2, n1, n2;
					for (m1 = 0; m1 <= 4; m1++)
					{
						for (n1 = 0; n1 <= 4; n1++)
						{
							if (ch2[k] == ch[m1][n1])break;
						}
						if (ch2[k] == ch[m1][n1])break;
					}
					for (m2 = 0; m2 <= 4; m2++)
					{
						for (n2 = 0; n2 <= 4; n2++)
						{
							if (ch2[k + 1] == ch[m2][n2])break;
						}
						if (ch2[k + 1] == ch[m2][n2])break;
					}
					m1 = m1 % 5;
					m2 = m2 % 5;
					if (n1 > 4) { n1 = n1 % 5; m1 = m1 + 1; }
					if (n2 > 4) { n2 = n2 % 5; m2 = m2 + 1; }
					if (m1 == m2)
					{
						ch2[k] = ch[m1][(n1 + 4) % 5];
						ch2[k + 1] = ch[m2][(n2 + 4) % 5];
					}
					else
					{
						if (n1 == n2)
						{
							ch2[k] = ch[(m1 + 4) % 5][n1];
							ch2[k + 1] = ch[(m2 + 4) % 5][n2];
						}
						else
						{
							ch2[k] = ch[m1][n2];
							ch2[k + 1] = ch[m2][n1];
						}
					}
					this_thread::sleep_for(chrono::microseconds(100));
				}
				auto end2 = chrono::high_resolution_clock::now();
				chrono::duration<float> duration2 = end2 - start2;
				cout << "Дешифрування:";
				for (int k = 0; k < strlen(ch2); k += 2)
				{
					 
					cout << ch2[k] << ch2[k + 1] << "";
					
					
				}
				cout << endl;
			
				/*st.afshifr3 = strdup(ch2);

		strcpy_s(st.afshifr3, ch2.c_str());*/

		ofstream jozef("E:\\time.txt"); //открываем файл для чтения
		jozef << duration2.count() << endl; //записываем в переменные содержание файла 
		jozef.close();
		ifstream file2("E:\\time.txt"); //открываем файл для чтения
		do
		{
			file2 >> tm.tcd; //записываем в переменные содержание файла 
		} while (!file2.eof());//пока не наступил конец файла
		file2.close();

		ofstream ofs;
		ofs.open("E:/time.txt", std::ofstream::out | std::ofstream::trunc); //очистка файла
		ofs.close();



		ofstream tim("E:/time2.txt", ios::binary | ios::app);
		tim.write((char*)&tm, sizeof(tm));
		tim.close();
		ofstream inf("E:/All3.dat", ios::binary | ios::app);
		inf.write((char*)&st, sizeof(st));
		inf.close();


		system("pause");
		system("cls");



		cout << endl << "Продовжуємо? (1-так/0-ні)";
		cmatch math2;
		string vibor;
		bool triger = false;
		do
		{


			cin.sync();
			getline(cin, vibor);
			regex  regular("([0-1]{1})");
			if (regex_match(vibor.c_str(), math2, regular))
			{

				triger = true;
			}
			else
			{
				cout << "Некоректне значення." << endl << "Повторіть введення:" << endl;

			}

		} while (!triger);
		vybor = stoi(math2[0]);
	}
}




void Edit()
{
	int x;
	string p, d;
	int otv, kolzap = 0;
	int a = 0;
	int i = 1;

	system("cls");


	while (i != 0)
	{
		system("cls");
		cout << endl << "Меню редагування ключа:";
		cout << endl << "1:Ключ Цезаря";
		cout << endl << "2:Ключ Виженера";
		cout << endl << "3:Ключ Плейфера";
		cout << endl << "0:Вихід до головного меню";
		cout << endl << endl << "Виберіть пункт меню: ";
		cin.sync();

		cmatch result;
		string vibor;
		bool flag = false;
		do
		{
			cin.sync();
			getline(cin, vibor);
			regex  regular("([0-8]{1})");
			if (regex_match(vibor.c_str(), result, regular))
			{
				flag = true;
			}
			else
			{
				cout << "Введений пункт меню не знайдено." << endl << "Повторіть введення:";
				//system("pause");
			}

		} while (!flag);
		a = stoi(result[0]);

		switch (a)
		{
		case 1: {
			cout << endl << "Ви дійсно хочете редагувати ключ? (1-так/0-ні)";
			cmatch result;
			string file;
			bool flag = false;
			do
			{


				cin.sync();
				getline(cin, file);
				regex  regular("([0-1]{1})");
				if (regex_match(file.c_str(), result, regular))
				{
					flag = true;
				}
				else
				{
					cout << "Некоректне зачення." << endl << "Повторіть введення:" << endl;
				}

			} while (!flag);
			otv = stoi(result[0]);

			if (otv == 1)
			{
				std::ofstream ofs;
				ofs.open("E:/numb.txt", std::ofstream::out | std::ofstream::trunc); //очистка файла
				ofs.close();

				ofstream file("E:\\numb.txt");
				cout << "Введіть новий ключ:";
				cmatch result;
				string shirfat;
				bool Trger = false;
				do
				{
					cin.sync();
					getline(cin, shirfat);
					regex  regular("([0-9]{0,99})");
					if (regex_match(shirfat.c_str(), result, regular))
					{
						Trger = true;
						
					}
					else
					{
						
						cout << "" << endl << "Повторіть введення:";
						//system("pause");
					}

				} while (!Trger);
				file << shirfat;
				shirfat = key1;
				file.close();
				cout << endl << "Ключ записано.";
				cout << endl << "Для виходу в меню натисніть будь-яку клавішу.";
				system("pause");

			}
			else
			{
				cout << endl << "Для виходу в меню натисніть будь-яку клавішу.";
				system("pause");
			}
			break;
		}
		case 2: {
			cout << endl << "Ви дійсно хочете редагувати ключ? (1-так/0-ні)";
			cmatch result;
			string file;
			bool flag = false;
			do
			{


				cin.sync();
				getline(cin, file);
				regex  regular("([0-1]{1})");
				if (regex_match(file.c_str(), result, regular))
				{
					flag = true;
				}
				else
				{
					cout << "Некоректне зачення." << endl << "Повторіть введення:" << endl;
				}

			} while (!flag);
			otv = stoi(result[0]);

			if (otv == 1)
			{
				std::ofstream ofs;
				ofs.open("E:/key.txt", std::ofstream::out | std::ofstream::trunc); //очистка файла
				ofs.close();

				ofstream file("E:\\key.txt");
				cout << "Введіть новий ключ:";
				cmatch math;
				string shif;
				bool Trger = false;
				do
				{
					cin.sync();
					getline(cin, shif);
					regex  regular("([A-Za-z]{0,50})");
					if (regex_match(shif.c_str(), math, regular))
					{
						Trger = true; 
					}
					else
					{
						cout << "" << endl << "Повторіть введення:";

						//system("pause");
					}

				} while (!Trger);
				file << shif;
				shif = key2;
				file.close();
				cout << endl << "Ключ записано.";
				cout << endl << "Для виходу в меню натисніть будь-яку клавішу.";
				system("pause");

			}
			else
			{
				cout << endl << "Для виходу в меню натисніть будь-яку клавішу.";
				system("pause");
			}
			break;
		}
		case 3: {
			cout << endl << "Ви дійсно хочете редагувати ключ? (1-так/0-ні)";
			cmatch result;
			string file;
			bool flag = false;
			do
			{


				cin.sync();
				getline(cin, file);
				regex  regular("([0-1]{1})");
				if (regex_match(file.c_str(), result, regular))
				{
					flag = true;
				}
				else
				{
					cout << "Некоректне зачення." << endl << "Повторіть введення:" << endl;
				}

			} while (!flag);
			otv = stoi(result[0]);

			if (otv == 1)
			{
				std::ofstream ofs;
				ofs.open("E:/key2.txt", std::ofstream::out | std::ofstream::trunc); //очистка файла
				ofs.close();

				ofstream file("E:\\key2.txt");
				cout << "Введіть новий ключ:";
				cmatch math;
				string shifrat;
				bool Trger = false;
				do
				{
					cin.sync();
					getline(cin, shifrat);
					regex  regular("([A-Za-z]{0,50})");
					if (regex_match(shifrat.c_str(), math, regular))
					{
						Trger = true;
						
					}
					else
					{
						cout << "" << endl << "Повторіть введення:";

						//system("pause");
					}

				} while (!Trger);
				file << shifrat;
				shifrat = key3;
				file.close();
				cout << endl << "Ключ записано.";
				cout << endl << "Для виходу в меню натисніть будь-яку клавішу.";
				system("pause");

			}
			else
			{
				cout << endl << "Для виходу в меню натисніть будь-яку клавішу.";
				system("pause");
			}
			break;
		}
		
		case 0: {
			cout << endl << "Выход в главное меню.";	system("pause");
			return;
		}
		}
	}



	
}







void Cesar()
{

	system("cls");
	conf st;
	int i(1);
	int b(0);
	int n(0);
	float max = 0;
	ifstream std("E:/All.dat", ios::binary | ios::in);
	if (!std)
	{
		cout << endl << "Файл не може бути відкритий.\n";
		system("pause");
		return;
	}
	int kolzap = 0;
	ifstream ss("E:/All.dat", ios::binary | ios::in);
	while (ss.read((char*)&st, sizeof(conf)))
		kolzap++;
	ss.close();
	if (kolzap == 0)
	{
		cout << endl << "Записи відсутні.\n";
		system("pause");
		return;
	}
	cout << " _____________________________________________________________________________________________________" << endl;
	cout << "|";
	cout.width(3); cout << "#";
	cout.width(3); cout << "|";
	cout.width(15); cout << setw(33) << right << "Повідомлення користувача";
	cout << "|";
	cout.width(30); cout << setw(30) << right << "Шифроване";
	cout << "|";
	cout.width(30); cout << setw(30) << right << "Дешифроване" << "|";
	//cout.width(17); cout << "Время работы шифратора" << "|";
	//cout.width(17); cout << "Время работы дешифратора" << "|";
	cout << endl;
	cout << "|_____|_________________________________|______________________________|______________________________|";
	while (std.read((char*)&st, sizeof(st)))
	{
		n++;
		cout << endl;
		//cout << "|";

		cout << "|";
		cout.width(3);
		cout << n;
		cout.width(3);
		cout << "|";
		//cout.width(3);
	//	cout << "|";
		cout.width(30);
		cout << setw(33) << right << st.shifr;
		cout << "|";
		cout.width(26);
		cout << setw(30) << right << st.deshifr;
		cout << "|";
		cout.width(26);
		cout << setw(30) << right << st.afshifr;
		cout << "|";



		cout << endl << "|_____|_________________________________|______________________________|______________________________|";
	}



	cout << endl << "Для виходу в меню натисніть будь-яку клавішу." << endl;
	system("pause");
	std.close();

}


void Vizhener()
{
	system("cls");
	conf st;
	int i(1);
	int b(0);
	int n(0);
	float max = 0;
	ifstream std("E:/All2.dat", ios::binary | ios::in);
	if (!std)
	{
		cout << endl << "Файл не може бути відкритий.\n";
		system("pause");
		return;
	}
	int kolzap = 0;
	ifstream ss("E:/All2.dat", ios::binary | ios::in);
	while (ss.read((char*)&st, sizeof(conf)))
		kolzap++;
	ss.close();
	if (kolzap == 0)
	{
		cout << endl << "Записи відсутні.\n";
		system("pause");
		return;
	}
	cout << " _____________________________________________________________________________________________________" << endl;
	cout << "|";
	cout.width(3); cout << "#";
	cout.width(3); cout << "|";
	cout.width(15); cout << setw(33) << right << "Повідомлення користувача";
	
	cout << "|";
	cout.width(30); cout << setw(30) << right << "Шифроване";
	cout << "|";
	cout.width(30); cout << setw(30) << right << "Дешифроване" << "|";
	//cout.width(17); cout << "Время работы шифратора" << "|";
	//cout.width(17); cout << "Время работы дешифратора" << "|";
	cout << endl;
	cout << "|_____|_________________________________|______________________________|______________________________|";
	while (std.read((char*)&st, sizeof(st)))
	{
		n++;
		cout << endl;
		//cout << "|";

		cout << "|";
		cout.width(3);
		cout << n;
		cout.width(3);
		cout << "|";
		//cout.width(3);
	//	cout << "|";
		cout.width(18);
		cout << setw(33) << right << st.vizhener;
	
		cout << "|";
		cout.width(15);
		cout << setw(30) << right << st.devizhener;
	
		cout << "|";
		cout.width(15);
		cout << setw(30) << right << st.afvizhener;
	
		cout << "|";



		cout << endl << "|_____|_________________________________|______________________________|______________________________|";
	}



	cout << endl << "Для виходу в меню натисніть будь-яку клавішу.\n" << endl;
	system("pause");
	std.close();
}


void Playfair()
{
	system("cls");
	conf st;
	int i(1);
	int b(0);
	int n(0);
	float max = 0;
	ifstream std("E:/All3.dat", ios::binary | ios::in);
	if (!std)
	{
		cout << endl << "Файл не може бути відкритий.\n";
		system("pause");
		return;
	}
	int kolzap = 0;
	ifstream ss("E:/All3.dat", ios::binary | ios::in);
	while (ss.read((char*)&st, sizeof(conf)))
		kolzap++;
	ss.close();
	if (kolzap == 0)
	{
		cout << endl << "Записи відсутні.\n";
		system("pause");
		return;
	}
	cout << " _____________________________________________________________________________________________________" << endl;
	cout << "|";
	cout.width(3); cout << "#";
	cout.width(3); cout << "|";
	cout.width(15); cout << setw(33) << right << "Повідомлення користувача";
	
	cout << "|";
	cout.width(30); cout << setw(30) << right << "Шифроване";
	cout << "|";
	cout.width(30); cout << setw(30) << right << "Дешифроване" << "|";
	//cout.width(17); cout << "Время работы шифратора" << "|";
	//cout.width(17); cout << "Время работы дешифратора" << "|";
	cout << endl;
	cout << "|_____|_________________________________|______________________________|______________________________|";
	while (std.read((char*)&st, sizeof(st)))
	{
		n++;
		cout << endl;
		//cout << "|";

		cout << "|";
		cout.width(3);
		cout << n;
		cout.width(3);
		cout << "|";
		//cout.width(3);
	//	cout << "|";
		cout.width(18);
		cout << setw(33) << right << st.shifr3;
	
		cout << "|";
		cout.width(15);
		cout << setw(30) << right << st.deshifr3;
	
		cout << "|";
		cout.width(15);
		cout << setw(30) << right << st.shifr3;
		
		cout << "|";



		cout << endl << "|_____|_________________________________|______________________________|______________________________|";
	}



	cout << endl << "Для виходу в меню натисніть будь-яку клавішу." << endl;
	system("pause");
	std.close();
}

void compare()   // доделать для каждого удачи
{
	system("cls");
	f9 st;
	char buffer[200];
	int j;
	int i(1);
	int b(0);
	int n(0);
	float max = 0;
	ifstream std("E:/time2.txt", ios::binary | ios::in);
	if (!std)
	{
		cout << endl << "Файл не може бути відкритий.\n";
		system("pause");
		return;
	}
	int kolzap = 0;
	ifstream ss("E:/time2.txt", ios::binary | ios::in);
	while (ss.read((char*)&st, sizeof(f9)))
		kolzap++;
	ss.close();
	if (kolzap == 0)
	{
		cout << endl << "Записи відсутні.\n";
		system("pause");
		return;
	}
	cout << " ___________________________________________________________________________________________________________________" << endl;
	cout << "|";
	cout.width(3); cout << "#";
	cout.width(3); cout << "|";
	cout.width(30); cout << setw(33) << right << "Назва методу";
	cout << "|";
	cout.width(30); cout << setw(30) << right << "Час роботи шифрування";
	cout << "|";
	cout.width(30); cout << setw(30) << right << "Час роботи дешифрування" << "|";
	cout.width(30); cout << setw(13) << right << "Довжина рядка" << "|"; 
	cout << endl;
	/*cout.width(15); cout << "      " << endl;*/
	cout << "|_____|_________________________________|______________________________|______________________________|_____________|";
	while (std.read((char*)&st, sizeof(st)))
	{ 
		
		n++;
		cout << endl;
		//cout << "|";

		cout << "|";
		cout.width(3);
		cout << n;
		cout.width(3);
		cout << "|";
		//cout.width(3);
	//	cout << "|";
		cout.width(10);
		cout.width(23);
		cout << setw(33) << right << st.tns;
		/*cout.width(8);*/
		cout << "|";
		
		cout.width(23);
		cout << setw(30) << right << st.tcs;
	/*	cout.width(5);*/ 
		cout << "|";
		cout.width(10);
		cout.width(23);
		cout << setw(30) << right << st.tcd;
	/*	cout.width(5);*/
		cout << "|";
		cout.width(10);
		cout.width(23);
		cout << setw(13) << right << st.len;
		/*	cout.width(5);*/
		cout << "|";



		cout << endl << "|_____|_________________________________|______________________________|______________________________|_____________|";
	}



	cout << endl << "Для виходу в меню натисніть будь-яку клавішу." << endl;
	system("pause");
	std.close();
}



void View()
{
	system("cls");

	int a = 0;
	int i = 1;
	while (i != 0)
	{
		system("cls");
		cout << endl << "Меню таблиц:";
		cout << endl << "1:Шифрование Цезаря";
		cout << endl << "2:Шифрование Виженера";
		cout << endl << "3:Шифрование Плейфера";
		cout << endl << "4:Порівняльна таблиця";
		cout << endl << "0:Вихід до головного меню";
		cout << endl << endl << "Виберіть пункт меню: ";
		cin.sync();

		cmatch result;
		string vibor;
		bool flag = false;
		do
		{
			cin.sync();
			getline(cin, vibor);
			regex  regular("([0-8]{1})");
			if (regex_match(vibor.c_str(), result, regular))
			{
				flag = true;
			}
			else
			{
				cout << "Введений пункт меню не знайдено." << endl << "Повторіть введення:";
				//system("pause");
			}

		} while (!flag);
		a = stoi(result[0]);

		switch (a)
		{
		case 1: {
			Cesar();
			break;
		}

		case 2: {
			Vizhener();
			break;
		}
		case 3: {
			Playfair();
			break;
		}
		case 4: {
			compare();
			break;
		}
		
		case 0: {
			cout << endl << "Выход в главное меню";	system("pause");
			return;
		}

		}
	}
}




void file()
{
	conf tp;
	f9 st;
	int otv, kolzap = 0;
	system("cls");


	int a = 0;
	int i = 1;
	while (i != 0)
	{
		system("cls");
		cout << endl << "Меню видалення файлу:";
		cout << endl << "1:Шифрование Цезаря";
		cout << endl << "2:Шифрование Виженера";
		cout << endl << "3:Шифрование Плейфера";
		cout << endl << "4:Поріняльна таблиця";
		cout << endl << "0:Вихід до головного меню";
		cout << endl << endl << "Виберіть пункт меню: ";
		cin.sync();

		cmatch result;
		string vibor;
		bool flag = false;
		do
		{
			cin.sync();
			getline(cin, vibor);
			regex  regular("([0-8]{1})");
			if (regex_match(vibor.c_str(), result, regular))
			{
				flag = true;
			}
			else
			{
				cout << "Введений пункт меню не знайдено." << endl << "Повторіть введення:";
				//system("pause");
			}

		} while (!flag);
		a = stoi(result[0]);

		switch (a)
		{
		case 1: {

			ifstream ss("E:/All.dat", ios::binary | ios::in);
			while (ss.read((char*)&tp, sizeof(conf)))
				kolzap++;
			ss.close();
			if (kolzap == 0)
			{
				cout << endl << "Введений пункт меню не знайдено";
				system("pause");
				return;
			}
			cout << endl << "Ви дійсно хочете очистити файл? Записані раніше дані будуть видалені. (1-так/0-ні)";
			cmatch result;
			string file;
			bool flag = false;
			do
			{


				cin.sync();
				getline(cin, file);
				regex  regular("([0-1]{1})");
				if (regex_match(file.c_str(), result, regular))
				{
					flag = true;
				}
				else
				{
					cout << "Некоректне зачення." << endl << "Повторіть введення:" << endl;
				}

			} while (!flag);
			otv = stoi(result[0]);

			if (otv == 1)
			{
				std::ofstream ofs;
				ofs.open("E:/All.dat", std::ofstream::out | std::ofstream::trunc); //очистка файла
				ofs.close();
				cout << endl << "Файл успішно очищений";
				cout << endl << "Для виходу в меню натисніть будь-яку клавішу.";
				system("pause");

			}
			else
			{
				cout << endl << "Для выхода в  меню нажмите любую клавишу.";
				system("pause");
			}
			break;
		}

		case 2: {
			ifstream ss("E:/All2.dat", ios::binary | ios::in);
			while (ss.read((char*)&tp, sizeof(conf)))
				kolzap++;
			ss.close();
			if (kolzap == 0)
			{
				cout << endl << "Введений пункт меню не знайдено";
				system("pause");
				return;
			}
			cout << endl << "Ви дійсно хочете очистити файл? Записані раніше дані будуть видалені. (1-так/0-ні)";
			cmatch result;
			string file;
			bool flag = false;
			do
			{


				cin.sync();
				getline(cin, file);
				regex  regular("([0-1]{1})");
				if (regex_match(file.c_str(), result, regular))
				{
					flag = true;
				}
				else
				{
					cout << "Некоректне зачення." << endl << "Повторіть введення:" << endl;
				}

			} while (!flag);
			otv = stoi(result[0]);

			if (otv == 1)
			{
				std::ofstream ofs;
				ofs.open("E:/All2.dat", std::ofstream::out | std::ofstream::trunc); //очистка файла
				ofs.close();
				cout << endl << "Файл успішно очищений";
				cout << endl << "Для виходу в меню натисніть будь-яку клавішу.";
				system("pause");

			}
			else
			{
				cout << endl << "Для выхода в  меню нажмите любую клавишу.";
				system("pause");
			}
			break;
		}
		case 3: {
			ifstream ss("E:/All3.dat", ios::binary | ios::in);
			while (ss.read((char*)&tp, sizeof(conf)))
				kolzap++;
			ss.close();
			if (kolzap == 0)
			{
				cout << endl << "Введений пункт меню не знайдено";
				system("pause");
				return;
			}
			cout << endl << "Ви дійсно хочете очистити файл? Записані раніше дані будуть видалені. (1-так/0-ні)";
			cmatch result;
			string file;
			bool flag = false;
			do
			{


				cin.sync();
				getline(cin, file);
				regex  regular("([0-1]{1})");
				if (regex_match(file.c_str(), result, regular))
				{
					flag = true;
				}
				else
				{
					cout << "Некоректне зачення." << endl << "Повторіть введення:" << endl;
				}

			} while (!flag);
			otv = stoi(result[0]);

			if (otv == 1)
			{
				std::ofstream ofs;
				ofs.open("E:/All3.dat", std::ofstream::out | std::ofstream::trunc); //очистка файла
				ofs.close();
				cout << endl << "Файл успішно очищений";
				cout << endl << "Для виходу в меню натисніть будь-яку клавішу.";
				system("pause");

			}
			else
			{
				cout << endl << "Для выхода в  меню нажмите любую клавишу.";
				system("pause");
			}
			break;
		}
		case 4: {
			ifstream ss("E:/time2.txt", ios::binary | ios::in);
			while (ss.read((char*)&st, sizeof(f9)))
				kolzap++;
			ss.close();
			if (kolzap == 0)
			{
				cout << endl << "Введений пункт меню не знайдено";
				system("pause");
				return;
			}
			cout << endl << "Ви дійсно хочете очистити файл? Записані раніше дані будуть видалені. (1-так/0-ні)";
			cmatch result;
			string file;
			bool flag = false;
			do
			{


				cin.sync();
				getline(cin, file);
				regex  regular("([0-1]{1})");
				if (regex_match(file.c_str(), result, regular))
				{
					flag = true;
				}
				else
				{
					cout << "Некоректне зачення." << endl << "Повторіть введення:" << endl;
				}

			} while (!flag);
			otv = stoi(result[0]);

			if (otv == 1)
			{
				std::ofstream ofs;
				ofs.open("E:/time2.txt", std::ofstream::out | std::ofstream::trunc); //очистка файла
				ofs.close();
				cout << endl << "Файл успішно очищений";
				cout << endl << "Для виходу в меню натисніть будь-яку клавішу.";
				system("pause");

			}
			else
			{
				cout << endl << "Для выхода в  меню нажмите любую клавишу.";
				system("pause");
			}
			break;
		}

		case 0: {
			cout << endl << "Выход в главное меню";	system("pause");
			return;
		}


		}

	}

}