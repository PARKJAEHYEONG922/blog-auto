"""
네이버 검색광고 파워링크 관리 API 클라이언트
"""
from typing import List, Dict, Any, Optional
from .base_client import NaverSearchAdBaseClient
from src.foundation.exceptions import NaverSearchAdAPIError
from src.foundation.logging import get_logger

logger = get_logger("vendors.naver.searchad.powerlink")


class PowerlinkClient(NaverSearchAdBaseClient):
    """파워링크 관리 API 클라이언트"""
    
    def __init__(self):
        super().__init__("powerlink", rate_limit=1.0)
        self._credentials = None
    
    def set_credentials(self, api_key: str, secret_key: str, customer_id: str):
        """API 인증 정보 설정"""
        self._credentials = {
            'api_key': api_key,
            'secret_key': secret_key, 
            'customer_id': customer_id
        }
        # config_manager에도 설정 (베이스 클라이언트에서 사용)
        from src.foundation.config import config_manager
        config = config_manager.load_api_config()
        config.searchad_access_license = api_key
        config.searchad_secret_key = secret_key
        config.searchad_customer_id = customer_id
    
    def get_supported_endpoints(self) -> List[str]:
        return [
            "/ncc/campaigns",
            "/ncc/adgroups", 
            "/ncc/keywords",
            "/ncc/ads",
            "/billing/bizmoney"
        ]
    
    def get_campaigns(self) -> List[Dict[str, Any]]:
        """캠페인 목록 조회"""
        try:
            response = self._make_request("/ncc/campaigns", "GET")
            return response if isinstance(response, list) else []
        except Exception as e:
            logger.error(f"캠페인 조회 실패: {e}")
            return []
    
    def get_campaign_details(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """캠페인 상세 정보 조회"""
        try:
            response = self._make_request(f"/ncc/campaigns/{campaign_id}", "GET")
            return response
        except Exception as e:
            logger.error(f"캠페인 상세 조회 실패 ({campaign_id}): {e}")
            return None
    
    def get_adgroups(self, campaign_id: str) -> List[Dict[str, Any]]:
        """광고그룹 목록 조회"""
        try:
            params = {"nccCampaignId": campaign_id}
            response = self._make_request("/ncc/adgroups", "GET", params=params)
            return response if isinstance(response, list) else []
        except Exception as e:
            logger.error(f"광고그룹 조회 실패 ({campaign_id}): {e}")
            return []
    
    def get_adgroup_details(self, adgroup_id: str) -> Optional[Dict[str, Any]]:
        """광고그룹 상세 정보 조회 (타겟팅 정보 포함)"""
        try:
            response = self._make_request(f"/ncc/adgroups/{adgroup_id}", "GET")
            return response
        except Exception as e:
            logger.error(f"광고그룹 상세 조회 실패 ({adgroup_id}): {e}")
            return None
    
    def get_keywords(self, adgroup_id: str) -> List[Dict[str, Any]]:
        """키워드 목록 조회"""
        try:
            params = {"nccAdgroupId": adgroup_id}
            response = self._make_request("/ncc/keywords", "GET", params=params)
            return response if isinstance(response, list) else []
        except Exception as e:
            logger.error(f"키워드 조회 실패 ({adgroup_id}): {e}")
            return []
    
    def get_ads(self, adgroup_id: str) -> List[Dict[str, Any]]:
        """광고 목록 조회"""
        try:
            params = {"nccAdgroupId": adgroup_id}
            response = self._make_request("/ncc/ads", "GET", params=params)
            return response if isinstance(response, list) else []
        except Exception as e:
            logger.error(f"광고 조회 실패 ({adgroup_id}): {e}")
            return []
    
    def get_bizmoney_balance(self) -> Optional[Dict[str, Any]]:
        """비즈머니 잔액 조회"""
        try:
            response = self._make_request("/billing/bizmoney", "GET")
            return response
        except Exception as e:
            logger.error(f"비즈머니 조회 실패: {e}")
            return None
    
    def update_keyword_status(self, keyword_id: str, user_lock: bool) -> bool:
        """키워드 상태 업데이트"""
        try:
            json_data = {"userLock": user_lock}
            params = {"fields": "userLock"}
            
            logger.info(f"=== 키워드 상태 변경 API 호출 시작 ===")
            logger.info(f"키워드 ID: {keyword_id}")
            logger.info(f"설정할 userLock: {user_lock}")
            logger.info(f"요청 URL: /ncc/keywords/{keyword_id}")
            logger.info(f"요청 데이터: {json_data}")
            logger.info(f"요청 파라미터: {params}")
            
            response = self._make_request(
                f"/ncc/keywords/{keyword_id}", 
                "PUT", 
                params=params,
                json_data=json_data
            )
            
            logger.info(f"API 응답: {response}")
            logger.info(f"응답 타입: {type(response)}")
            
            # 응답 검증
            if response and isinstance(response, dict):
                updated_user_lock = response.get('userLock')
                logger.info(f"응답에서 받은 userLock: {updated_user_lock}")
                
                if updated_user_lock == user_lock:
                    logger.info(f"✅ 키워드 상태 변경 성공: {keyword_id} -> userLock={updated_user_lock}")
                    return True
                else:
                    logger.warning(f"⚠️ 키워드 상태 변경 불일치: 요청={user_lock}, 응답={updated_user_lock}")
                    return False
            else:
                logger.warning(f"⚠️ 응답이 예상 형식이 아님: {response}")
                # 응답이 없거나 다른 형식이어도 일단 성공으로 처리
                return True
            
        except Exception as e:
            logger.error(f"❌ 키워드 상태 업데이트 실패 ({keyword_id}): {e}")
            logger.error(f"요청 상세: userLock={user_lock}, endpoint=/ncc/keywords/{keyword_id}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return False
    
    def update_keyword_bid(self, keyword_id: str, adgroup_id: str, bid_amount: int) -> bool:
        """키워드 입찰가 업데이트"""
        try:
            json_data = {
                "nccAdgroupId": adgroup_id,
                "bidAmt": bid_amount,
                "useGroupBidAmt": False
            }
            params = {"fields": "bidAmt,nccAdgroupId,useGroupBidAmt"}
            response = self._make_request(
                f"/ncc/keywords/{keyword_id}",
                "PUT",
                params=params, 
                json_data=json_data
            )
            return True
        except Exception as e:
            logger.error(f"키워드 입찰가 업데이트 실패 ({keyword_id}): {e}")
            return False
    
