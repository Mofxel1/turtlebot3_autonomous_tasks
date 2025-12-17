#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import actionlib
import yaml
import os
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from actionlib_msgs.msg import GoalStatus

class WaypointNavigator:
    def __init__(self):
        rospy.init_node('kobuki_waypoint_navigation')
        
        # Move Base İstemcisi
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        rospy.loginfo("Navigasyon sistemi (move_base) bekleniyor... Lütfen bekleyin.")
        self.client.wait_for_server()
        rospy.loginfo("Sistem Hazır! YAML Dosyası okunuyor... 📂")

    def load_mission_from_yaml(self):
        """
        YAML dosyasını script'in bulunduğu konuma göre dinamik olarak bulur.
        """
        try:
            # 1. Şu an çalışan scriptin klasörünü bul (.../scripts/)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 2. Bir üst klasöre çık (Paket kök dizini)
            package_root = os.path.dirname(script_dir)
            
            # 3. Config klasörüne gir
            file_path = os.path.join(package_root, "config", "gorev_listesi.yaml")
            
            rospy.loginfo(f"Dosya yolu şurada aranıyor: {file_path}")

            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
                rospy.loginfo(f"YAML başarıyla yüklendi! ✅")
                return data
        except Exception as e:
            rospy.logerr(f"YAML dosyası okunamadı! Hata: {e}")
            return None

    def send_goal(self, x, y):
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        
        # Koordinatlar
        goal.target_pose.pose.position.x = float(x)
        goal.target_pose.pose.position.y = float(y)
        goal.target_pose.pose.position.z = 0.0
        
        # Yönelim (Düz duruş)
        goal.target_pose.pose.orientation.w = 1.0 
        goal.target_pose.pose.orientation.z = 0.0

        rospy.loginfo(f"➡️  Hedefe Gidiliyor: X={x}, Y={y}")
        self.client.send_goal(goal)
        
        # Robot gidene kadar bekle
        self.client.wait_for_result()
        
        # Sonucu kontrol et
        if self.client.get_state() == GoalStatus.SUCCEEDED:
            rospy.loginfo("✅ HEDEFE VARILDI!")
            return True
        else:
            rospy.logwarn("❌ HEDEFE GİDİLEMEDİ! (Engel olabilir)")
            return False

    def start_mission(self):
        # 1. YAML Dosyasını Yükle
        mission_data = self.load_mission_from_yaml()
        if not mission_data:
            return # Dosya yoksa dur

        # NOT: initial_pose kısmı kaldırıldı.
        
        # 2. Waypoint Listesini YAML'dan al ve gez
        if 'waypoints' in mission_data:
            waypoints = mission_data['waypoints']
            
            print(f"\n🚀 TOPLAM {len(waypoints)} HEDEF VAR.")
            
            for i, point in enumerate(waypoints):
                print(f"\n--- Hedef {i+1} / {len(waypoints)} ---")
                # YAML listesi [x, y] formatında
                self.send_goal(point[0], point[1])
                
                # Her hedefe varınca 1 saniye bekle
                rospy.sleep(1)

            print("\n🏆 TÜM GÖREVLER TAMAMLANDI! 🏆")
        else:
            rospy.logerr("YAML dosyasında 'waypoints' listesi bulunamadı!")

if __name__ == '__main__':
    try:
        navigator = WaypointNavigator()
        navigator.start_mission()
    except rospy.ROSInterruptException:
        pass
