��    K      t  e   �      `     a     s     �     �     �  	   �     �     �     �  ^        d  +   z     �     �     �  2   �               %  !   8  �   Z  i   	     �	  
   �	  -   �	     �	     �	     �	     	
  �   &
     �
     �
  !   �
  �        �     �            	   '     1  D   C  D   �  7   �       	     "        A  *   _     �     �     �     �  E   �  ^   =     �  �   �  =   {  �   �  %   S      y  V   �     �       z     #   �  2   �  $   �  
                  /     <  .   D  1   s  �  �     `  !   �     �  !   �     �        4     ;   I     �  ~   �  8   !  T   Z     �     �  F   �  u        �     �     �  D   �  �    �   �  
   �     �  d   �  @     /   T  /   �  C   �  O  �  H   H     �  W   �  !     ?   "  .   b  :   �     �     �  %   �  �      �   �      B!     �!     �!  O   �!  -   @"  J   n"  &   �"  +   �"  )   #  %   6#  �   \#  �   $  7   �$  h  �$  |   U&  �   �&  C   �'  <   �'  �   7(  #   �(     �(  �   �(  ?   �)  ]   *  K   l*     �*     �*     �*     �*     �*  g   +  X   t+     (   1              	   *                  2      8               $                
   5   .   3   :          9             "   ?         ;   G   0   F   H       '                B      E   )   <   6                         /               4   J   !   %   I   C          A       ,   &   -          K           >      +   @   =       7                 #       D              
The found files:   %s (maybe error)   %s (maybe ok)  MB available space  MB needed space  nothing!  size to be backed up:   to make a back-up! * * * WARNING * * * A recording is currently running. Please stop the recording before trying to start a flashing. Additional backup ->  BACK-UP TOOL, FOR MAKING A COMPLETE BACK-UP Backup > HDD Backup > USB Backup done with:  Backup finished and copied to your USB-flashdrive. BackupSuite Create: kerneldump Create: root.ubifs Do you really want to unpack %s ? Do you want to make a back-up on USB?

This only takes a few minutes depending on the used filesystem and is fully automatic.

Make sure you first insert an USB flash drive before you select Yes. Do you want to make an USB-back-up image on HDD? 

This only takes a few minutes and is fully automatic.
 Exit Flashing:  For flashing your receiver files are needed:
 Full back-up direct to USB Full back-up on HDD Full back-up to USB Full back-up to the harddisk If you place an USB-stick containing this file then the back-up will be automatically made onto the USB-stick and can be used to restore the current image if necessary. Image creation FAILED! KB per second Make a backup or restore a backup Most likely this back-up can't be restored because of it's size, it's simply too big to restore. This is a limitation of the bootloader not of the back-up or the BackupSuite. NOT found files for flashing!
 No supported receiver found! Not enough free space on  Only kernel Only root PLEASE READ THIS: Please be patient, a backup will now be made, this will take about:  Please check the manual of the receiver on how to restore the image. Please: DO NOT reboot your STB and turn off the power.
 Restore backup Run flash Select parameter for start flash!
 Select the folder with backup Show only found image and mtd partitions.
 Simulate (no write) Some information about the task Standard (root and kernel) The content of the folder is: The image or kernel will be flashing and auto booted in few minutes.
 The program will abort, please try another medium with more free space to create your back-up. The program will exit now. There COULD be a problem with restoring this back-up because the size of the back-up comes close to the maximum size. This is a limitation of the bootloader not of the back-up or the BackupSuite. There is NO valid USB-stick found, so I've got nothing to do. There is a valid USB-flashdrive detected in one of the USB-ports, therefore an extra copy of the back-up image will now be copied to that USB-flashdrive. This only takes about 20 seconds..... Time required for this process:  To back-up directly to the USB-stick, the USB-stick MUST contain a file with the name: USB Image created in:  Unzip Warning!
Use at your own risk! Make always a backup before use!
Don't use it if you use multiple ubi volumes in ubi layer! What is new since the last release? Your STB will freeze during the flashing process.
 and there is made an extra copy in:  available  backupstick or backupstick.txt current:  %s minutes not found, the backup process will be aborted! ofgwrite will stop enigma2 now to run the flash.
 Project-Id-Version: BackupSuite
Report-Msgid-Bugs-To: 
PO-Revision-Date: 
Last-Translator: Мартин Петков <marto74bg@yahoo.co.uk>
Language-Team: Bulgarian
Language: bg
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
X-Poedit-SourceCharset: UTF-8
X-Generator: Poedit 2.1.1
Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);
 
Открити файлове:   %s (може би грешка)   %s (може би е ок  МБ свободно място  МБ са необходими  нищо няма!  размер на резервното копие:   за да се създаде резервно копие! * * * ВНИМАНИЕ * * * В момента тече запис. Моля спрете го, преди да започнете с флашването. Допълнително резервно копие ->  ПРОГРАМА ЗА СЪЗДАВАНЕ НА ПЪЛНО РЕЗЕРВНО КОПИЕ Бакъп > HDD Бакъп > USB Резервното копие завърши със скорост:  Резервното копие завърши и файловете са копирани на USB флашката. BackupSuite Създава се: kerneldump Създава се: root.ubifs Наистина ли искате да разопаковате %s? Наистина ли искате да направите резервно копие на USB?

Това ще отнеме само няколко минути в зависимост от файловата система и процеса е напълно автоматизиран.

Убедете се, че сте поставили USB флашка, преди да изберете Да. Наистина ли искате да направите резервно копие на HDD? 

Това ще отнеме само няколко минути, процеса е напълно автоматизиран.
 Изход Флашване:  За флашването наВашия приемник са необходими файлове:
 Пълно резервно копие директно на USB Пълно резервно копие на HDD Пълно резервно копие на USB Пълно резервно копие на твърдия диск Ако включите USB-флашка съдържаща този файл, то резервното копие ще бъде автоматично създадено на USB-флашката и, може да се използва за възстановяване на текущия имидж при необходимост. Създаването на имиджа завърши с ГРЕШКА! КБ в секунда Създаване или възстановяване на резервно копие Най-вероятно, този бакъп не може да се възстанови поради неговия размер, т.к. е твърде голям. Това е ограничение на bootloadeа, а не на резервното копие или на BackupSuite. НЕ са открити файлове за флашване!
 Приемника не се поддържа! Недостатъчно свободно място на  Само ядро Само имидж МОЛЯ ПРОЧЕТЕТЕ ТОВА: Моля бъдете търпеливи, създаването на резервно копие започна, това ще отнеме около:  Моля проверете инструкциите на приемника относно, как да възстановите имиджа. Моля, НЕ рестартирайте Вашия приемник и НЕ изключвайте захранването!
 Възстановяване Флашване Изберете параметри за старт на флашването!
 Изберете папката с бакъп Покажи само откритите имиджи и mtd дялове
 Симулирай (без запис) Някои данни за задачата Стандарт (имидж и ядро) Съдържание на папка: Имиджа или ядрото ще бъдат презаписани и приемника автоматично ще се
рестартира след няколко минути.
 Процеса ще прекъсне, моля опитайте с друг носител, на който има повече свободно място. Програмата ще се затвори сега. Може да възникне проблем с възстановяването на това резервно копие поради това ,че размера му се доближава до максимално възможния. Това ограничение е на bootloader-а а не на резервното копие или BackupSuite. Открит е невалиден USB-стик, затова резервно копие няма да се направи. Открит е валиден USB-стик в един от USB-портовете, затова допълнително резервно копие на имиджа ще бъде копирано на този USB-стик. Това ще отнеме само около 20 секунди... Време необходимо за този процес:  За директно копиране на USB-флашка, Флашката ТРЯБВА да съдържа файл с име: USB имджа е създан в:  Разархивиране Важно!
Използвайте на свой риск! Винаги правете бакъп преди използване!
Не го използвайте, ако имате няколко ubi дяла! Какво ново след последната версия? Вашия приемник ще замръзне по време на флашването!
 и направи допълнително резервно копие в:  достъпен  backupstick или backupstick.txt текуща:  %s минути не е открит, процеса за резервно копие ще бъде прекратен! програмата ofgwrite сега ще спре enigma2 за флашването!
 